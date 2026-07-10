#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Communicate with the EU Data Act portal of volkswagen group."""

import re
import os
import json
import logging
import asyncio
import xmltodict
from copy import deepcopy
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED
import csv

from sys import version_info, argv
from datetime import timedelta, datetime, timezone
from urllib.parse import parse_qs, urlparse
import aiohttp
from bs4 import BeautifulSoup, ResultSet
from .utilities import json_loads
from .eudavehicle import EUDAVehicle
from .exceptions import (
    PyCupraConfigException,
    PyCupraAuthenticationException,
    PyCupraAccountLockedException,
    PyCupraEUDAPermissionExpiredException,
    PyCupraException,
    PyCupraEULAException,
    PyCupraLoginFailedException,
    PyCupraInvalidRequestException,
    PyCupraMarketingConsentException,
    # PyCupraRequestInProgressException,
    # PyCupraServiceUnavailable
)

from aiohttp import ClientSession, ClientTimeout
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT, METH_DELETE
from http import cookies

from .const import (
    DATA_DIRECTORY,
    AUTH_OIDCONFIG,
    EUDA_CLIENT_LIST,
    # EUDA_AUTH_OIDC,
    # EUDA_AUTH_ISSUER,
    EUDA_HEADERS_AUTH,
    EUDA_HEADERS_SESSION,
    EUDA_BASE_URL,
    EUDA_API_VEHICLES,
    EUDA_API_DATACLUSTERS,
    EUDA_API_FILE_LIST,
    EUDA_API_FILE_DOWNLOAD,
    EUDA_API_TOKEN,
    EUDA_API_PERMISSION_CHECK,
    EUDA_API_LOGOUT,
    EUDA_URL_DETAILS,
    EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY,
    EUDA_SHORT_TERM_DATA_MILEAGE_KEY,
    EUDA_SHORT_TERM_DATA_TRAVEL_TIME_KEY,
    EUDA_SHORT_TERM_DATA_AVERAGE_FUEL_CONSUMPTION_KEY,
    EUDA_SHORT_TERM_DATA_AVERAGE_ELECTR_ENGINE_CONSUMPTION_KEY,
    EUDA_SHORT_TERM_DATA_AVERAGE_GAS_CONSUMPTION_KEY,
)

version_info >= (3, 0) or exit("Python 3 required")

_LOGGER = logging.getLogger(__name__)
BRAND_CUPRA = "cupra"
TIMEOUT = timedelta(seconds=30)
loginInProgress = False


class EUDAConnection:
    """Connection to Connect services"""

    # Init connection class
    def __init__(
        self,
        session: ClientSession,
        brand: str = "cupra",
        username: str = "",
        password: str = "",
        fulldebug: bool = False,
        anonymise: bool = True,
        logPrefix=None,
        hass=None,
        **optional,
    ):
        """Initialize"""
        self._logPrefix = logPrefix
        if self._logPrefix is not None:
            self._LOGGER = logging.getLogger(__name__ + "_" + self._logPrefix)
        else:
            self._LOGGER = _LOGGER

        self._session = session
        self._lock = asyncio.Lock()
        self._session_fulldebug = fulldebug
        self._session_anonymise = anonymise
        self._session_headers = EUDA_HEADERS_SESSION.copy()
        self._session_auth_headers = EUDA_HEADERS_AUTH.copy()
        self._session_cookies: cookies.SimpleCookie = cookies.SimpleCookie()
        self._session_first_update = False
        self._session_auth_brand = brand
        self._session_auth_username = username
        self._session_auth_password = password
        self._vehicles: list = []
        self._hass = hass

        self._anonymisationDict: dict = {}
        self.addToAnonymisationDict(
            self._session_auth_username, "[USERNAME_ANONYMISED]"
        )
        self.addToAnonymisationDict(
            self._session_auth_password, "[PASSWORD_ANONYMISED]"
        )
        self._anonymisationKeys = {"firstName", "lastName", "dateOfBirth", "nickname"}
        self.addToAnonymisationKeys("name")
        self.addToAnonymisationKeys("given_name")
        self.addToAnonymisationKeys("email")
        self.addToAnonymisationKeys("family_name")
        self.addToAnonymisationKeys("birthdate")
        self.addToAnonymisationKeys("vin")
        self._error401 = False
        self._error403 = False
        self._loginError: str | None = None
        # for file processing and information extraction
        self.rawData: dict = {}
        self.currentData: dict = {}
        self.tripData: dict = {}
        try:
            if self._hass:
                self._dataBasePath = self._hass.config.path(DATA_DIRECTORY)
            else:
                self._dataBasePath = os.path.join(".", DATA_DIRECTORY)
            if not os.path.exists(self._dataBasePath):
                self._LOGGER.error(
                    f"Directory {self._dataBasePath} does not exist. This should only happen once. Creating it."
                )
                os.mkdir(self._dataBasePath)
            self._dataFolder = os.path.join(self._dataBasePath, "euda_files")
            if not os.path.exists(self._dataFolder):
                self._LOGGER.error(
                    f"Directory {self._dataFolder} does not exist. This should only happen once. Creating it."
                )
                os.mkdir(self._dataFolder)
            self._dataFolderInProcess = os.path.join(self._dataFolder, "in_process")
            if not os.path.exists(self._dataFolderInProcess):
                os.mkdir(self._dataFolderInProcess)
            self._dataFolderProcessed = os.path.join(self._dataFolder, "processed")
            if not os.path.exists(self._dataFolderProcessed):
                os.mkdir(self._dataFolderProcessed)
            self._dataFolderErrorFiles = os.path.join(self._dataFolder, "error_files")
            if not os.path.exists(self._dataFolderErrorFiles):
                os.mkdir(self._dataFolderErrorFiles)
            self._dataFolderArchive = os.path.join(self._dataFolder, "archive")
            if not os.path.exists(self._dataFolderArchive):
                os.mkdir(self._dataFolderArchive)
            self._lastArchiveTime = datetime.now(tz=None) - timedelta(
                days=1
            )  # Set the last archive time to 24 hours ago.
        except Exception as error:
            raise PyCupraException(
                f"Error while checking for data folders and creating them if bot already present. Error: {error}"
            )

    def _clear_cookies(self):
        self._session._cookie_jar._cookies.clear()
        self._session_cookies = cookies.SimpleCookie()

    # API login/logout/authorization
    async def doLogin(self, **data) -> bool:
        """Login method, clean login or use token from file and refresh it"""
        # Remove cookies and re-init session
        self._clear_cookies()
        self._vehicles.clear()
        self._session_headers = EUDA_HEADERS_SESSION.copy()
        self._session_auth_headers = EUDA_HEADERS_AUTH.copy()

        # self._LOGGER.info('Initiating new login with user name and password.')
        return await self._authorize(self._session_auth_brand)

    async def _authorize(self, client: str = BRAND_CUPRA) -> bool:
        """ "Login" function. Authorize a certain client type and get cookies."""
        # Login/Authorization starts here
        try:
            self._LOGGER.debug("Checking for concurrent logins in progress")

            waitTimeExpired = datetime.now(tz=None) + timedelta(seconds=15)
            global loginInProgress
            while loginInProgress:
                await asyncio.sleep(5)
                if waitTimeExpired < datetime.now(tz=None):
                    self._LOGGER.warning(
                        "Waited about 15 seconds for a concurrent login to finish without success. Assuming, it has ended."
                    )
                    loginInProgress = False
            loginInProgress = True

            self._LOGGER.debug(f"Starting authorization process for client {client}")
            req = await self._session.get(url=AUTH_OIDCONFIG)
            if req.status != 200:
                self._LOGGER.debug(
                    f"Get request to {AUTH_OIDCONFIG} was not successful. Response: {req}"
                )
                return False
            response_data = await req.json()
            self._LOGGER.debug(
                f"Get request to {AUTH_OIDCONFIG} was not successful. Response data: {response_data}"
            )
            auth_issuer = response_data["issuer"]
            auth_oidc = response_data["authorization_endpoint"]
            # authorization_url = EUDA_AUTH_OIDC + "?client_id=" + EUDA_CLIENT_LIST[client]['CLIENT_ID'] + "&response_type=code&scope="
            authorization_url = (
                auth_oidc
                + "?client_id="
                + EUDA_CLIENT_LIST[client]["CLIENT_ID"]
                + "&response_type=code&scope="
            )
            authorization_url = (
                authorization_url
                + EUDA_CLIENT_LIST[client]["SCOPE"]
                + "&state=de__en__"
                + client.upper()
                + "&redirect_uri="
            )
            authorization_url = (
                authorization_url
                + EUDA_CLIENT_LIST[client]["REDIRECT_URL"]
                + "&prompt=login"
            )

            req = await self._session.get(
                url=authorization_url,
                headers=self._session_auth_headers,
                allow_redirects=False,
            )
            if req.headers.get("Location", False):
                ref = req.headers.get("Location", "")
                if "error" in ref:
                    error = parse_qs(urlparse(ref).query).get("error", "")[0]
                    if "error_description" in ref:
                        error = parse_qs(urlparse(ref).query).get(
                            "error_description", ""
                        )[0]
                        self._LOGGER.info(f"Unable to login, {error}")
                    else:
                        self._LOGGER.info("Unable to login.")
                    raise PyCupraException(error)
                else:
                    if self._session_fulldebug:
                        self._LOGGER.debug(f'Got authorization endpoint: "{ref}"')
                    req = await self._session.get(
                        url=ref,
                        headers=self._session_auth_headers,
                        allow_redirects=False,
                    )
            if req.headers.get("Location", False):
                ref = req.headers.get("Location", "")
                if "error" in ref:
                    error = parse_qs(urlparse(ref).query).get("error", "")[0]
                    if "error_description" in ref:
                        error = parse_qs(urlparse(ref).query).get(
                            "error_description", ""
                        )[0]
                        self._LOGGER.info(f"Unable to login, {error}")
                    else:
                        self._LOGGER.info("Unable to login.")
                    raise PyCupraException(error)
                else:
                    if self._session_fulldebug:
                        self._LOGGER.debug(f'Got authorization endpoint: "{ref}"')
                    req = await self._session.get(
                        url=ref,
                        headers=self._session_auth_headers,
                        allow_redirects=False,
                    )
            if req.status != 200:
                # self._LOGGER.debug(f'Get request to {EUDA_AUTH_OIDC} was not successful. Response: {req}')
                self._LOGGER.debug(
                    f"Get request to {auth_oidc} was not successful. Response: {req}"
                )
                return False
            # If we need to sign in
            if "signin-service" in ref:
                self._LOGGER.debug("Got redirect to signin-service")
                # location = await self._signin_service(req, EUDA_AUTH_ISSUER, EUDA_AUTH_OIDC)
                location = await self._signin_service(
                    req, auth_issuer, auth_oidc, client
                )
            else:
                # We are already logged on, shorter authorization flow
                location = req.headers.get("Location", None)

            # Follow all redirects until we reach the callback URL
            try:
                maxDepth = 10
                while not location.startswith(EUDA_CLIENT_LIST[client]["REDIRECT_URL"]):
                    if location is None:
                        raise PyCupraException("Login failed")
                    if "error" in location:
                        errorTxt = parse_qs(urlparse(location).query).get("error", "")[
                            0
                        ]
                        if errorTxt == "login.error.throttled":
                            timeout = parse_qs(urlparse(location).query).get(
                                "enableNextButtonAfterSeconds", ""
                            )[0]
                            self._loginError = (
                                f"Account is locked for another {timeout} seconds"
                            )
                            raise PyCupraAccountLockedException(
                                f"Account is locked for another {timeout} seconds"
                            )
                        elif errorTxt == "login.errors.password_invalid":
                            self._loginError = "Invalid credentials"
                            raise PyCupraAuthenticationException("Invalid credentials")
                        else:
                            self._LOGGER.warning(f"Login failed: {errorTxt}")
                        self._loginError = f"Login failed: {errorTxt}"
                        raise PyCupraLoginFailedException(errorTxt)
                    if "terms-and-conditions" in location:
                        self._loginError = 'The terms and conditions must be accepted first at your local SEAT/Cupra site, e.g. "https://cupraid.vwgroup.io/"'
                        raise PyCupraEULAException(
                            'The terms and conditions must be accepted first at your local SEAT/Cupra site, e.g. "https://cupraid.vwgroup.io/"'
                        )
                    if "consent/marketing" in location:
                        self._loginError = 'The question to consent to marketing must be answered first at your local SEAT/Cupra site, e.g. "https://cupraid.vwgroup.io/"'
                        raise PyCupraMarketingConsentException(
                            'The question to consent to marketing must be answered first at your local SEAT/Cupra site, e.g. "https://cupraid.vwgroup.io/"'
                        )
                    if (
                        "user_id" in location
                    ):  # Get the user_id which is needed for some later requests
                        self._user_id = parse_qs(urlparse(location).query).get(
                            "user_id", [""]
                        )[0]
                        self.addToAnonymisationDict(
                            self._user_id, "[USER_ID_ANONYMISED]"
                        )
                        # self._LOGGER.debug('Got user_id: %s' % self._user_id)
                    if self._session_fulldebug:
                        self._LOGGER.debug(
                            self.anonymise(f'Following redirect to "{location}"')
                        )
                    response = await self._session.get(
                        url=location,
                        headers=self._session_auth_headers,
                        allow_redirects=False,
                    )
                    if response.headers.get("Location", False) is False:
                        self._LOGGER.debug(f"Unexpected response: {await req.text()}")
                        raise PyCupraAuthenticationException(
                            "User appears unauthorized"
                        )
                    location = response.headers.get("Location", None)
                    # Set a max limit on requests to prevent forever loop
                    maxDepth -= 1
                    if maxDepth == 0:
                        raise PyCupraException("Too many redirects")
            except (
                PyCupraException,
                PyCupraEULAException,
                PyCupraAuthenticationException,
                PyCupraAccountLockedException,
                PyCupraLoginFailedException,
                PyCupraMarketingConsentException,
            ):
                self._LOGGER.warning(
                    f"Running into login problems with location={location}"
                )
                raise
            except Exception as e:
                # If we get an unhandled exception it should be because we can't redirect to the EUDA_BASE_URL and thus we have our auth code
                if "code" in location:
                    if self._session_fulldebug:
                        self._LOGGER.debug("Got code: %s" % location)
                    pass
                else:
                    self._LOGGER.debug("Exception occured while logging in.")
                    raise PyCupraLoginFailedException(e)

            # Login at identity portal successful. Now following callback to user.html of EU Data Act portal
            self._LOGGER.debug("Following call back to get authorisation cookies.")
            self._clear_cookies()

            req = await self._session.get(
                url=location, headers=self._session_auth_headers, allow_redirects=False
            )
            if req.headers.get("Location", False):
                ref = req.headers.get("Location", "")
                if "error" in ref:
                    error = parse_qs(urlparse(ref).query).get("error", "")[0]
                    if "error_description" in ref:
                        error = parse_qs(urlparse(ref).query).get(
                            "error_description", ""
                        )[0]
                        self._LOGGER.info(f"Unable to login, {error}")
                    else:
                        self._LOGGER.info("Unable to login.")
                    raise PyCupraException(error)
                else:
                    if self._session_fulldebug:
                        self._LOGGER.debug(f'Got url: "{ref}"')
                    req = await self._session.get(
                        url=ref,
                        headers=self._session_auth_headers,
                        allow_redirects=False,
                    )
            # Update cookie jar
            # if self._session_cookies != '':
            #    self._session_cookies.update(req.cookies)
            # else:
            #    self._session_cookies = req.cookies
            self._session_cookies.update(req.cookies)

            if req.headers.get("Location", False):
                ref = req.headers.get("Location", "")
                if "error" in ref:
                    error = parse_qs(urlparse(ref).query).get("error", "")[0]
                    if "error_description" in ref:
                        error = parse_qs(urlparse(ref).query).get(
                            "error_description", ""
                        )[0]
                        self._LOGGER.info(f"Unable to login, {error}")
                    else:
                        self._LOGGER.info("Unable to login.")
                    raise PyCupraException(error)
                else:
                    if self._session_fulldebug:
                        self._LOGGER.debug(f'Got url: "{ref}"')
                    req = await self._session.get(
                        url=ref,
                        headers=self._session_auth_headers,
                        allow_redirects=False,
                    )

            if req.headers.get("Location", False):
                ref = req.headers.get("Location", "")
                if "error" in ref:
                    error = parse_qs(urlparse(ref).query).get("error", "")[0]
                    if "error_description" in ref:
                        error = parse_qs(urlparse(ref).query).get(
                            "error_description", ""
                        )[0]
                        self._LOGGER.info(f"Unable to login, {error}")
                    else:
                        self._LOGGER.info("Unable to login.")
                    raise PyCupraException(error)
                else:
                    if self._session_fulldebug:
                        self._LOGGER.debug(f'Got url: "{ref}"')
                    req = await self._session.get(
                        url=ref,
                        headers=self._session_auth_headers,
                        allow_redirects=False,
                    )

            if req.status != 200:
                self._LOGGER.debug(
                    f"Walking through redirects was not successful. Response: {req}"
                )
                return False
        except PyCupraEULAException:
            self._LOGGER.warning(
                'Login failed, the terms and conditions might have been updated and need to be accepted. Login to  your local SEAT/Cupra site, e.g. "https://cupraid.vwgroup.io/" and accept the new terms before trying again'
            )
            raise
        # except (PyCupraMarketingConsentException):
        #    self._LOGGER.warning('Login failed, the marketing conditions might have been updated and need to be accepted or disagreed. Login to  your local SEAT/Cupra site, e.g. "https://cupraid.vwgroup.io/" and accept the new terms before trying again')
        #    raise
        except PyCupraAccountLockedException:
            self._LOGGER.warning(
                "Your account is locked, probably because of too many incorrect login attempts. Make sure that your account is not in use somewhere with incorrect password"
            )
            raise
        except PyCupraAuthenticationException:
            self._LOGGER.warning(
                "Invalid credentials or invalid configuration. Make sure you have entered the correct credentials"
            )
            raise
        except PyCupraException:
            self._LOGGER.error(
                "An API error was encountered during login, try again later"
            )
            raise
        except TypeError:
            self._LOGGER.warning(
                self.anonymise(
                    f'Login failed for {self._session_auth_username}. The server might be temporarily unavailable, try again later. If the problem persists, verify your account at your local SEAT/Cupra site, e.g. "https://cupraofficial.se/"'
                )
            )
        except Exception as error:
            self._LOGGER.error(
                self.anonymise(
                    f"Login failed for {self._session_auth_username}, {error}"
                )
            )
            loginInProgress = False
            return False
        loginInProgress = False
        return True

    async def _signin_service(
        self,
        html: aiohttp.ClientResponse,
        authissuer: str,
        authorizationEndpoint: str,
        client: str,
    ) -> Any:
        """Method to signin to Connect portal."""
        # Extract login form and extract attributes
        try:
            response_data = await html.text()
            responseSoup = BeautifulSoup(response_data, "html.parser")
            form_data = dict()
            if responseSoup is None:
                raise PyCupraLoginFailedException(
                    "Login failed, server did not return a login form"
                )
            pageElement: Any = responseSoup.find("form", id="emailPasswordForm")
            for t in pageElement.find_all("input", type="hidden"):
                if self._session_fulldebug:
                    self._LOGGER.debug(
                        f"Extracted form attribute: {t['name'], t['value']}"
                    )
                form_data[t["name"]] = t["value"]
            form_data["email"] = self._session_auth_username
            pe_url = authissuer + pageElement.get("action")
        except Exception as e:
            self._LOGGER.error(f"Failed to extract user login form. Error: {e}")
            raise

        # POST email
        self._session_auth_headers["Referer"] = authorizationEndpoint
        self._session_auth_headers["Origin"] = authissuer
        self._LOGGER.debug(
            self.anonymise(
                f"Start authorization for user {self._session_auth_username}"
            )
        )
        req = await self._session.post(
            url=pe_url, headers=self._session_auth_headers, data=form_data
        )
        if req.status != 200:
            raise PyCupraException("Authorization request failed")
        try:
            response_data = await req.text()
            responseSoup = BeautifulSoup(response_data, "html.parser")
            pwform = {}
            credentials_form: Any = responseSoup.find("form", id="credentialsForm")
            all_scripts: ResultSet = responseSoup.find_all("script", {"src": False})
            if credentials_form is not None:
                self._LOGGER.debug("Found HTML credentials form, extracting attributes")
                for t in credentials_form.find_all("input", type="hidden"):
                    if self._session_fulldebug:
                        self._LOGGER.debug(
                            f"Extracted form attribute: {t['name'], t['value']}"
                        )
                    pwform[t["name"]] = t["value"]
                    form_data = pwform
                    post_action = credentials_form.get("action")
            elif all_scripts is not None:
                self._LOGGER.debug(
                    "Found dynamic credentials form, extracting attributes"
                )
                pattern: re.Pattern[str] = re.compile("templateModel: (.*?),\n")
                for sc in all_scripts:
                    patternSearchResult = pattern.search(sc.string)
                    if patternSearchResult is not None:
                        import json

                        data = patternSearchResult  # pattern.search(sc.string)
                        jsondata = json.loads(data.groups()[0])
                        self._LOGGER.debug(self.anonymise(f"JSON: {jsondata}"))
                        if not jsondata.get("hmac", False):
                            raise PyCupraLoginFailedException(
                                "Failed to extract login hmac attribute"
                            )
                        if not jsondata.get("postAction", False):
                            raise PyCupraLoginFailedException(
                                "Failed to extract login post action attribute"
                            )
                        if jsondata.get("error", None) is not None:
                            raise PyCupraLoginFailedException(
                                f"Login failed with error: {jsondata.get('error', None)}"
                            )
                        form_data["hmac"] = jsondata.get("hmac", "")
                        post_action = jsondata.get("postAction")
            else:
                raise PyCupraLoginFailedException("Failed to extract login form data")
            form_data["password"] = self._session_auth_password
        except PyCupraLoginFailedException:
            raise
        except Exception as e:
            raise PyCupraAuthenticationException(
                f"Invalid username or service unavailable. Error: {e}"
            )

        # POST password
        self._session_auth_headers["Referer"] = pe_url
        self._session_auth_headers["Origin"] = authissuer
        self._LOGGER.debug("Finalizing login")

        client_id = EUDA_CLIENT_LIST[client]["CLIENT_ID"]
        pp_url = authissuer + "/" + post_action
        if "signin-service" not in pp_url or client_id not in pp_url:
            pp_url = authissuer + "/signin-service/v1/" + client_id + "/" + post_action

        if self._session_fulldebug:
            self._LOGGER.debug(f'Using login action url: "{pp_url}"')
        req = await self._session.post(
            url=pp_url,
            headers=self._session_auth_headers,
            data=form_data,
            allow_redirects=False,
        )
        return req.headers.get("Location", None)

    async def terminate(self) -> None:
        """Log out from connect services"""
        await self.logout()

    async def logout(self) -> None:
        """Logout, revoke tokens."""
        self._LOGGER.info("Initiating logout.")
        url = EUDA_API_LOGOUT.format(baseurl=EUDA_BASE_URL)
        # response = await self.get(url)
        response = await self._session._request(
            method=METH_GET,
            str_or_url=url,
            headers=self._session_headers,
            cookies=self._session_cookies,
        )
        if response.status != 200:
            self._LOGGER.error(
                f'Request for "{url}" returned with status code [{response.status}], response: {response}'
            )
            raise PyCupraException(
                f"http.get for logout failed. Response status: {response.status}"
            )
        self._LOGGER.info(
            f"Sent logout call to API. Response status = {response.status}"
        )
        self._clear_cookies()

    # HTTP methods to API
    async def get(self, url: str, vin="") -> Any:
        """Perform a HTTP GET."""
        try:
            response = await self._request(METH_GET, url)
            return response
        except aiohttp.client_exceptions.ClientResponseError as error:
            data = {
                "status_code": error.status,
                "error": error.code,
                "error_description": error.message,
                "response_headers": error.headers,
                "request_info": error.request_info,
            }
            if error.status == 401:
                self._LOGGER.warning(
                    'Received "Unauthorized" while fetching data. This can occur if login expired.'
                )
                if True:  # not self._error401:
                    self._error401 = True
                    try:
                        rc = await self._authorize(self._session_auth_brand)
                        if rc:
                            self._LOGGER.info("Successful relogin after error 401.")
                            self._error401 = False
                            return data  # Leave get() without debug output of http request information
                        else:
                            self._LOGGER.info(
                                "Refresh of tokens after error 401 not successful."
                            )
                    except Exception as e:
                        self._LOGGER.error(
                            f"Error when reauthorising after error 401. Error: {e}"
                        )
                        self._LOGGER.info(
                            "Refresh of tokens after error 401 not successful."
                        )
            if error.status == 403:
                self._LOGGER.warning(
                    'Received "Forbidden" while fetching data. This can occur if login expired.'
                )
                if True:  # self._error403 != True:
                    self._error403 = True
                    try:
                        rc = await self._authorize(self._session_auth_brand)
                        if rc:
                            self._LOGGER.info("Successful relogin after error 403.")
                            self._error403 = False
                            return data  # Leave get() without debug output of http request information
                        else:
                            self._LOGGER.info(
                                "Refresh of tokens after error 403 not successful."
                            )
                    except Exception as e:
                        self._LOGGER.error(
                            f"Error when reauthorising after error 403. Error: {e}"
                        )
                        self._LOGGER.info(
                            "Refresh of tokens after error 403 not successful."
                        )
            elif error.status == 400:
                self._LOGGER.error(
                    'Received "Bad Request" from server. The request might be malformed or not implemented correctly for this vehicle.'
                )
            elif error.status == 404:
                self._LOGGER.debug(
                    'Received "Not found". Possibly the request was looking for something, that is not available.'
                )
            elif error.status == 412:
                self._LOGGER.debug(
                    'Received "Pre-condition failed". Service might be temporarily unavailable.'
                )
            elif error.status == 500:
                self._LOGGER.info(
                    'Received "Internal server error". The service is temporarily unavailable.'
                )
            elif error.status == 502:
                self._LOGGER.info(
                    'Received "Bad gateway". Either the endpoint is temporarily unavailable or not supported for this vehicle.'
                )
            elif error.status == 503:
                self._LOGGER.info(
                    'Received "Service unavailable". Possibly the server is overloaded or down for maintenance.'
                )
            elif 400 <= error.status <= 499:
                self._LOGGER.error(
                    f"Received unhandled error {error.status} indicating client-side problem.\nRestart or try again later."
                )
            elif 500 <= error.status <= 599:
                self._LOGGER.error(
                    f"Received unhandled error {error.status} indicating server-side problem.\nThe service might be temporarily unavailable."
                )
            else:
                self._LOGGER.error(
                    f"Received unhandled error {error.status} while requesting API endpoint."
                )
            self._LOGGER.debug(self.anonymise(f"HTTP request information: {data}"))
            return data
        except Exception as e:
            self._LOGGER.debug(f"Got non HTTP related error: {e}")
            return {"error_description": "Non HTTP related error"}

    async def post(self, url: str, **data) -> Any:
        """Perform a HTTP POST."""
        if data:
            return await self._request(METH_POST, url, **data)
        else:
            return await self._request(METH_POST, url)

    async def _request(self, method: str, url: str, **kwargs) -> Any:
        """Perform a HTTP query"""
        if self._session_fulldebug:
            argsString = ""
            if len(kwargs) > 0:
                argsString = "with "
                for k, val in kwargs.items():
                    argsString = argsString + f"{k}='{val}' "
            self._LOGGER.debug(self.anonymise(f'HTTP {method} "{url}" {argsString}'))
        async with self._session.request(
            method,
            url,
            headers=self._session_headers,
            timeout=ClientTimeout(total=TIMEOUT.seconds),
            cookies=self._session_cookies,
            raise_for_status=False,
            **kwargs,
        ) as response:
            response.raise_for_status()

            # Update cookie jar
            # if self._session_cookies != '':
            #    self._session_cookies.update(response.cookies)
            # else:
            #    self._session_cookies = response.cookies
            self._session_cookies.update(response.cookies)
            res: Any = {}

            try:
                if response.status == 204:
                    res = {"status_code": response.status}
                elif response.status == 202 and method == METH_PUT:
                    res = response
                elif response.status == 200 and method == METH_DELETE:
                    res = response
                elif 200 <= response.status <= 299:
                    # If this is a revoke token url, expect Content-Length 0 and return
                    if (
                        int(response.headers.get("Content-Length", 0)) == 0
                        and "revoke" in url
                    ):
                        if response.status == 200:
                            return True
                        else:
                            return False
                    else:
                        if "xml" in response.headers.get("Content-Type", ""):
                            res = xmltodict.parse(await response.text())
                        elif "application/octet-stream" in response.headers.get(
                            "Content-Type", ""
                        ):
                            res = await response.content.read()
                        elif "text/html" in response.headers.get("Content-Type", ""):
                            res = await response.content.read()
                        else:
                            res = await response.json(loads=json_loads)
                else:
                    res = {}
                    self._LOGGER.debug(
                        self.anonymise(
                            f"Not success status code [{response.status}] response: {response}"
                        )
                    )
            except Exception as e:
                res = {}
                self._LOGGER.debug(
                    self.anonymise(
                        f"Something went wrong [{response.status}] response: {response}, error: {e}"
                    )
                )
                return res

            if self._session_fulldebug:
                if (
                    "application/octet-stream"
                    in response.headers.get("Content-Type", "")
                ) or ("text/html" in response.headers.get("Content-Type", "")):
                    self._LOGGER.debug(
                        self.anonymise(
                            f'Request for "{url}" returned with status code [{response.status}]. Not showing response for the Content-Type of this response.'
                        )
                    )
                elif method == METH_PUT or method == METH_DELETE:
                    # deepcopy() of res can produce errors, if res is the API response on PUT or DELETE
                    self._LOGGER.debug(
                        f'Request for "{self.anonymise(url)}" returned with status code [{response.status}]. Not showing response for http {method}'
                    )
                else:
                    self._LOGGER.debug(
                        self.anonymise(
                            f'Request for "{url}" returned with status code [{response.status}], response: {self.anonymise(deepcopy(res))}'
                        )
                    )
            else:
                self._LOGGER.debug(
                    f'Request for "{url}" returned with status code [{response.status}]'
                )
            return res

    async def _data_call(self, query: str, **data) -> Any:
        """Function for POST actions with error handling."""
        try:
            response = await self.post(query, **data)
            self._LOGGER.debug(self.anonymise(f"Data call returned: {response}"))
            return response
        except aiohttp.client_exceptions.ClientResponseError as error:
            self._LOGGER.debug(
                self.anonymise(
                    f"Request failed. Data: {data}, HTTP request headers: {self._session_headers}"
                )
            )
            if error.status == 401:
                self._LOGGER.error("Unauthorized")
            elif error.status == 400:
                self._LOGGER.error("Bad request")
            elif error.status == 429:
                self._LOGGER.warning(
                    "Too many requests. Further requests can only be made after the end of next trip in order to protect your vehicles battery."
                )
                return 429
            elif error.status == 500:
                self._LOGGER.error(
                    "Internal server error, server might be temporarily unavailable"
                )
            elif error.status == 502:
                self._LOGGER.error(
                    "Bad gateway, this function may not be implemented for this vehicle"
                )
            else:
                self._LOGGER.error(f"Unhandled HTTP exception: {error}")
            # return False
        except Exception as error:
            self._LOGGER.error(f"Failure to execute: {error}")
        return False

    async def checkPermission(self, baseurl: str, vin: str = "") -> bool:
        try:
            url = EUDA_API_TOKEN.format(baseurl=EUDA_BASE_URL)
            # response = await self.get(url)
            response = await self._session._request(
                method=METH_GET,
                str_or_url=url,
                headers=self._session_headers,
                cookies=self._session_cookies,
            )
            if response.status >= 400:
                self._LOGGER.error("Get token.json failed.")
                raise PyCupraException("http.get to fetch token.json failed")

            url = EUDA_API_PERMISSION_CHECK.format(baseurl=EUDA_BASE_URL)
            # response = await self.get(url)
            response = await self._session._request(
                method=METH_GET,
                str_or_url=url,
                headers=self._session_headers,
                cookies=self._session_cookies,
            )
            if response.status != 200:
                self._LOGGER.error(
                    f'Request for "{url}" returned with status code [{response.status}], response: {response}'
                )
                raise PyCupraException(
                    f"http.get for permission check failed. Response status: {response.status}"
                )

            if vin != "":
                response = await self.get(
                    EUDA_URL_DETAILS.format(baseurl=baseurl, vin=vin)
                )
            return True
        except Exception as error:
            self._LOGGER.error(f"Error in checkPermission. Error: {error}")
            raise PyCupraEUDAPermissionExpiredException(
                "Error while checking permission."
            )
        return False

    async def getVehicles(self) -> dict:
        """Get the vehicles for the account that is logged in."""
        data = {}
        try:
            # if not await self.checkPermission(baseurl):
            #    raise 'Permission check failed'
            response = await self.get(
                EUDA_API_VEHICLES.format(baseurl=EUDA_BASE_URL, viewPos="FRONT_LEFT")
            )
            if len(response) > 0:
                data["vehicles"] = response
            elif response == []:
                data["vehicles"] = []
            elif response.get("status_code", {}):
                self._LOGGER.warning(
                    f"Could not fetch vehicles, HTTP status code: {response.get('status_code')}"
                )
            else:
                self._LOGGER.info("Unhandled error while trying to fetch vehicles")
        except Exception as error:
            self._LOGGER.warning(f"Could not fetch vehicles, error: {error}")
            return data

        # If API returns no vehicles, raise an error
        if len(data) == 0:
            raise PyCupraConfigException("No vehicles were found for given account!")
        # Get vehicle connectivity information
        else:
            try:
                for vehicle in data["vehicles"]:
                    self._LOGGER.debug(
                        self.anonymise(
                            f"Checking vehicle {vehicle.get('nickName', '')}"
                        )
                    )
                    # Only vehicles with role='PRIMARY_USER' and enrollmentStatus='COMPLETED' are valid
                    if (
                        vehicle.get("role", "") == "PRIMARY_USER"
                        and vehicle.get("enrollmentStatus", "") == "COMPLETED"
                    ):
                        vin: str = vehicle.get("vin", "")
                        self.addToAnonymisationDict(vin, "[VIN_ANONYMISED]")
                        nickName = vehicle.get("nickName", "")
                        newVehicle = {
                            "vin": vin,
                            "brand": self._session_auth_brand,
                            "nickName": nickName,
                            "logPrefix": self._logPrefix,
                        }
                        # Check if object already exist
                        self._LOGGER.debug("Check if vehicle exists")
                        if self.vehicle(vin) is not None:
                            self._LOGGER.debug(
                                self.anonymise(
                                    f"Vehicle with VIN number {vin} already exist."
                                )
                            )
                            car = EUDAVehicle(self, newVehicle)
                            if not car == self.vehicle(vin):
                                self._LOGGER.debug(
                                    self.anonymise(f"Updating {newVehicle} object")
                                )
                                self._vehicles.remove(self.vehicle(vin))
                                self._vehicles.append(EUDAVehicle(self, newVehicle))
                        else:
                            self._LOGGER.debug(self.anonymise(f"Adding vehicle {vin}"))
                            self._vehicles.append(EUDAVehicle(self, newVehicle))
                    else:
                        self._LOGGER.debug(
                            self.anonymise(
                                f"Vehicle {vehicle.get('vin', '')} can not be used. Role={vehicle.get('role', '')}, enrollment status={vehicle.get('enrollmentStatus', '')}"
                            )
                        )
            except PyCupraConfigException:
                raise
            except Exception:
                raise PyCupraInvalidRequestException(
                    "Unable to fetch associated vehicles for account"
                )
        return data

    async def getDatacluster(self, baseurl: str, vin: str, type: str) -> dict:
        """Get information for a data cluster."""
        data = {}
        try:
            if not await self.checkPermission(baseurl, vin):
                raise PyCupraEUDAPermissionExpiredException("Permission check failed")
            response = await self.get(
                EUDA_API_DATACLUSTERS.format(baseurl=baseurl, vin=vin, type=type)
            )
            if response.get("Name", "") != "":
                data[type] = response
            elif response.get("status_code", {}) == 404 and type == "partial":
                self._LOGGER.error(
                    f"Could not find a customised data request for your account, HTTP status code: {response.get('status_code')}. Did you forget to create one?"
                )
            elif response.get("status_code", {}):
                self._LOGGER.info(
                    f"Could not fetch data cluster information for cluster type '{type}', HTTP status code: {response.get('status_code')}"
                )
            else:
                self._LOGGER.info(
                    f"Unhandled error while trying to fetch data cluster information for cluster type '{type}'."
                )
        except Exception as error:
            self._LOGGER.error(
                f"Could not fetch data cluster information for cluster type '{type}'. Error: {error}"
            )
            raise PyCupraInvalidRequestException(
                "Unable to fetch data cluster information"
            )
        return data

    async def getListOfAvailableFiles(
        self, baseurl: str, vin: str, identifier: str, type: str
    ) -> dict:
        """Get list of the available data files on the portal."""
        data = {}
        try:
            self._session_headers["type"] = type
            response = await self.get(
                EUDA_API_FILE_LIST.format(baseurl=baseurl, vin=vin, id=identifier)
            )
            self._session_headers.pop("type")
            if isinstance(response, list):
                if len(response) > 0:
                    data["availableDataFiles"] = response
            elif response.get("status_code", {}):
                self._LOGGER.warning(
                    f"Could not fetch list of available data files, HTTP status code: {response.get('status_code')}"
                )
            else:
                self._LOGGER.info(
                    "Unhandled error while trying to fetch list of available data files"
                )
        except Exception as error:
            self._LOGGER.warning(
                f"Could not fetch list of available data files, error: {error}"
            )
            if self._session_headers.get("type", None) is not None:
                self._session_headers.pop("type")
            raise PyCupraInvalidRequestException(
                "Unable to fetch list of available data files"
            )
        return data

    async def getOneDatafile(
        self, filename: str, baseurl: str, vin: str, identifier: str, type: str
    ) -> bytes:
        """Get one data file"""
        try:
            self._session_headers["filename"] = filename
            self._session_headers["type"] = type
            fileContent: bytes = await self._request(
                METH_GET,
                url=EUDA_API_FILE_DOWNLOAD.format(
                    baseurl=baseurl, vin=vin, id=identifier
                ),
            )
            self._session_headers.pop("type")
            self._session_headers.pop("filename")
            return fileContent
        except Exception:
            self._LOGGER.debug(self.anonymise(f"Could not fetch data file {filename}."))
            if self._session_headers.get("type", None) is not None:
                self._session_headers.pop("type")
            if self._session_headers.get("filename", None) is not None:
                self._session_headers.pop("filename")
            # raise PyCupraInvalidRequestException("Unable to download data file")
        return bytes(0)

    def writeDataFile(self, fileNameWithPath: str, fileContent) -> bool:
        try:
            if os.path.isfile(fileNameWithPath):
                self._LOGGER.debug(
                    self.anonymise(
                        f"File {fileNameWithPath} is already present. Not overwrinting it."
                    )
                )
            else:
                with open(fileNameWithPath, "wb") as f:
                    f.write(fileContent)
                f.close()
            return True
        except Exception as e:
            self._LOGGER.warning(
                f"writeDataFile() not successful. Ignoring this problem. Error: {e}"
            )
            return False

    #### Functions, that process the downloaded files and extract the information
    async def update(self, vin: str | None = None) -> bool:
        """To be called regularly to get new files from the portal and to process them"""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.checkForFilesInProcess, vin)

            await self.getData(vin)

            if not await self.processFiles(vin):
                _LOGGER.warning(
                    "Call processFiles() was not successful. Ignoring this problem."
                )

            return True
        except Exception as e:
            if vin is None:
                self._LOGGER.error(f"update() not successful. Error: {e}")
            else:
                self._LOGGER.error(
                    f"update() not successful for vehicle {vin}. Error: {e}"
                )
        return False

    async def addFileToZipArchive(self, fileFolder: str, fileName: str) -> bool:
        try:
            zipFileName = os.path.join(
                self._dataFolderArchive,
                GetVINFromFileName(fileName)
                + "_"
                + datetime.strftime(GetTimeStampFromFileName(fileName), "%Y%m")
                + ".zip",
            )
            if not os.path.exists(zipFileName):
                self._LOGGER.debug(
                    f"Zip file {zipFileName} does not exist. Creating it"
                )
            with ZipFile(zipFileName, "a", compression=ZIP_DEFLATED) as fzip:
                # if len(fzip.namelist())<1:
                #    self._LOGGER.debug(f'Zip file {zipFileName} is empty. Creating it')
                if fileName in fzip.namelist():
                    self._LOGGER.debug(
                        f"File {fileName} already present in zip file {zipFileName}. Should not happen, but no problem."
                    )
                else:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None, fzip.write, os.path.join(fileFolder, fileName), fileName
                    )
            return True
        except Exception as e:
            self._LOGGER.warning(f"readZipFile() not successful. Error: {e}")
            return False

    async def archiveFiles(self, vin: str | None = None) -> bool:
        """Archive EUDA files older than 10 days in the archive folder"""
        try:
            now = datetime.now(tz=None)
            compareDate = (
                datetime(year=now.year, month=now.month, day=now.day)
                - timedelta(days=10)
            ).astimezone(None)
            # Loop over files in 'processed' folder
            loop = asyncio.get_running_loop()
            filesInProcessedDir = await loop.run_in_executor(
                None, os.listdir, str(self._dataFolderProcessed)
            )
            if len(filesInProcessedDir) > 0:
                counter = 0
                for entryName in filesInProcessedDir:
                    if GetTimeStampFromFileName(entryName) < compareDate:
                        if vin is None or vin in entryName:
                            if await self.addFileToZipArchive(
                                self._dataFolderProcessed, entryName
                            ):
                                os.remove(
                                    os.path.join(self._dataFolderProcessed, entryName)
                                )
                                counter = counter + 1
                            else:
                                self._LOGGER.error(
                                    f"Failed to add file {entryName} to zip archive. Keeping it in processed files folder."
                                )
                self._LOGGER.debug(
                    f"Moved {counter} files from 'processed' folder to archive."
                )
                return True
        except Exception as e:
            self._LOGGER.warning(f"archiveFiles() not successful. Error: {e}")
        return False

    async def processFiles(self, vin: str | None = None) -> bool:
        """Process files in 'euda_files' folder, move them to 'in_process' folder and then extract trip information from raw data"""
        try:
            loop = asyncio.get_running_loop()
            filesInDir = await loop.run_in_executor(None, os.scandir, self._dataFolder)
            for entry in filesInDir:
                if entry.is_file():
                    if vin is None or vin in entry.name:
                        await self.processSingleFile(entry)
            self._LOGGER.debug("Finished reading files.")
            if not self.extractTripsFromRawData():
                self._LOGGER.warning(
                    "Extraction of trips from raw data was not successful."
                )
                return False
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.writeTripStatisticsFile, vin)

            # Check, if self.rawData is empty
            if self.rawData == {}:
                # Call extractInformationFromFile for the latest file from the processed folder, so that self.rawData has one entry
                newestTimestamp = GetTimeStampFromFileName("Dummy_20000101000000.json")
                newestEntry = None
                loop = asyncio.get_running_loop()
                filesInProcessedDir = await loop.run_in_executor(
                    None, os.scandir, self._dataFolderProcessed
                )
                for entry in filesInProcessedDir:
                    if entry.is_file():
                        if vin is None or vin in entry.name:
                            if GetTimeStampFromFileName(entry.name) > newestTimestamp:
                                newestTimestamp = GetTimeStampFromFileName(entry.name)
                                newestEntry = entry
                if newestEntry is not None:
                    await self.extractInformationFromFile(newestEntry)
                    self._LOGGER.debug(
                        self.anonymise(
                            f"Extracted information from {newestEntry.name} to initialise rawData dict."
                        )
                    )

            # Copy currentData and tripData for each vehicle in the vehicle itself
            for vehicle in self.vehicles:
                if vin is None or vehicle.vin == vin:
                    vehicle.currentData = self.currentData.get(vehicle.vin, {})
                    vehicle.tripData = self.tripData.get(vehicle.vin, {})
                    vehicle.calcLatestTripSumValues(sumType="day")
                    vehicle.calcLatestTripSumValues(sumType="month")

            # Move processed files from 'in_process' folder to 'processed' folder
            loop = asyncio.get_running_loop()
            filesInProcessDir = await loop.run_in_executor(
                None, os.listdir, str(self._dataFolderInProcess)
            )
            if len(filesInProcessDir) > 0:
                counter = 0
                for entryName in filesInProcessDir:
                    if vin is None or vin in entryName:
                        os.replace(
                            os.path.join(self._dataFolderInProcess, entryName),
                            os.path.join(self._dataFolderProcessed, entryName),
                        )
                        counter = counter + 1
                self._LOGGER.debug(
                    f"Moved {counter} files from 'in_process' folder to 'processed' folder."
                )

            # Archiving
            if self._lastArchiveTime + timedelta(days=1) < datetime.now(tz=None):
                # Time to call for archiving
                if not await self.archiveFiles(vin):
                    _LOGGER.warning(
                        "Call archiveFiles() was not successful. Ignoring this problem."
                    )
                else:
                    self._lastArchiveTime = datetime.now(tz=None)

            return True
        except Exception as e:
            raise PyCupraException(f"processFiles() encountered an error. Error: {e}")
        return False

    # async def checkForFilesInProcess(self) -> bool:
    def checkForFilesInProcess(self, vin: str | None = None) -> bool:
        try:
            filesInDir = os.listdir(self._dataFolderInProcess)
            if len(filesInDir) > 0:
                counter = 0
                for entryName in filesInDir:
                    if vin is None or vin in entryName:
                        os.replace(
                            os.path.join(self._dataFolderInProcess, entryName),
                            os.path.join(self._dataFolder, entryName),
                        )
                        counter = counter + 1
                self._LOGGER.warning(
                    f"Found {counter} files in the 'in_process' folder. Moved them back data folder to process them again."
                )
            return True
        except Exception as e:
            raise PyCupraException(
                f"checkForFilesInProcess() encountered an error. Error: {e}"
            )
        return False

    async def processSingleFile(self, fileObj):
        try:
            if await self.extractInformationFromFile(fileObj):
                os.rename(
                    fileObj.path, os.path.join(self._dataFolderInProcess, fileObj.name)
                )
            else:
                self._LOGGER.info(
                    self.anonymise(
                        f"extractInformationFromFile not successful for '{fileObj.name}'. Keeping the file"
                    )
                )
        except Exception as e:
            raise PyCupraException(
                f"processSingleFile() encountered an error. Error: {e}"
            )

    async def readDataFile(self, fileObj):
        try:
            if fileObj.is_file():
                with open(fileObj, mode="r") as f:
                    dataString = f.read()
                    f.close()
                data = json.loads(dataString)
                return data, fileObj.name
            self._LOGGER.info(self.anonymise(f"No data file '{fileObj.name}' present."))
            return None, fileObj.name
        except Exception as e:
            self._LOGGER.warning(f"readDataFile() not successful. Error: {e}")
            return None, ""

    async def readZipFile(self, zipFileObj):
        try:
            with ZipFile(zipFileObj) as fzip:
                if len(fzip.namelist()) < 1:
                    self._LOGGER.warning("Zip file is empty. No data found")
                    return None, ""
                with fzip.open(fzip.infolist()[0].filename) as f:
                    dataString = f.read()
                    f.close()
                data = json.loads(dataString)
                return data, fzip.infolist()[0].filename
            self._LOGGER.info(
                self.anonymise(f"No data file '{zipFileObj.name}' present.")
            )
            return None, ""
        except Exception as e:
            self._LOGGER.warning(f"readZipFile() not successful. Error: {e}")
            return None, ""

    async def extractInformationFromFile(self, fileObj) -> bool:
        """Method to read one data file and gather its information"""
        try:
            if fileObj.path.find(".zip") > 0:
                # fileObj is a zip file
                dataFromFile, fileName = await self.readZipFile(fileObj)
            else:
                dataFromFile, fileName = await self.readDataFile(fileObj)
            if not dataFromFile:
                self._LOGGER.debug(
                    self.anonymise(
                        f"Could not read data file '{fileObj.name}' or it is empty."
                    )
                )
                return False
            if len(dataFromFile.get("Data", [])) == 0:
                self._LOGGER.debug(
                    self.anonymise(
                        f"Data section of file '{fileObj.name}' is empty."
                    )
                )
                return False
            # self._LOGGER.debug('Copying data from single file to raw data dict.')
            vin = GetVINFromFileName(fileName)
            timeStamp = GetTimeStampFromFileName(fileName)
            if self.rawData.get(vin, None) is None:
                self.rawData[vin] = {}
            if self.currentData.get(vin, None) is None:
                self.currentData[vin] = {}
            if self.rawData.get(vin, {}).get(timeStamp, None) is None:
                self.rawData[vin][timeStamp] = dataFromFile
                if (
                    self.currentData.get(vin, {}).get(
                        "timeStamp",
                        GetTimeStampFromFileName("Dummy_20000101000000.json"),
                    )
                    <= timeStamp
                    and len(dataFromFile.get("Data", [])) > 0
                ):
                    # Time stamp of current file is equal or later than time stamp of self.currentData
                    self.currentData[vin]["timeStamp"] = timeStamp
                    self.currentData[vin]["Data"] = dataFromFile.get("Data", [])
                else:
                    if len(dataFromFile.get("Data", [])) < 1:
                        self._LOGGER.info(f"Data list of file {fileName} is empty.")
                    else:
                        self._LOGGER.info(
                            f"Timestamp of file {fileName} is {timeStamp} which is not newer than"
                            f"{self.currentData.get(vin, {}).get('timeStamp', GetTimeStampFromFileName('Dummy_20000101000000.json'))}."
                        )
            else:
                self._LOGGER.error(
                    "Wanted to copy data to raw data dict, but timestamp is already present."
                )
            return True
        except Exception as e:
            raise PyCupraException(
                f"extractInformationFromFile() encountered an error. Error: {e}"
            )
        return False

    def extractTripsFromRawData(self) -> bool:
        try:
            for vehicle in self.vehicles:
                dataPointList = self.rawData.get(vehicle.vin, {})
                for timeStamp in dataPointList:
                    dataPoint = self.rawData.get(vehicle.vin, {}).get(timeStamp, {})
                    dataKeyList = dataPoint.get("Data", [])
                    tripElement: dict[str, Any] = {}
                    for element in dataKeyList:
                        if (
                            element.get("key", "")
                            == EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY
                        ):
                            tripElement["startMileage"] = int(element.get("value", "0"))
                        if element.get("key", "") == EUDA_SHORT_TERM_DATA_MILEAGE_KEY:
                            tripElement["distance"] = int(element.get("value", "0"))
                        if (
                            element.get("key", "")
                            == EUDA_SHORT_TERM_DATA_TRAVEL_TIME_KEY
                        ):
                            tripElement["travelTime"] = int(element.get("value", "0"))
                            timeStampString = element.get("timestampUtc", "")
                            try:
                                if timeStampString != "":
                                    tripElement["tripEnd"] = (
                                        datetime.strptime(
                                            timeStampString, "%Y-%m-%dT%H:%M:%S.%fZ"
                                        )
                                        .replace(tzinfo=timezone.utc)
                                        .astimezone(None)
                                    )
                                else:
                                    tripElement["tripEnd"] = timeStamp
                                    self._LOGGER.warning(
                                        self.anonymise(
                                            f"Failed to read time stamp of tripElement vehicle {vehicle.vin}. Using time stamp of data file. {tripElement}"
                                        )
                                    )
                            except Exception as e:
                                self._LOGGER.error(
                                    self.anonymise(
                                        f"Error while trying to convert time stamp string {timeStampString} to datetime. Error: {e}"
                                    )
                                )
                                tripElement["tripEnd"] = timeStamp

                        if (
                            element.get("key", "")
                            == EUDA_SHORT_TERM_DATA_AVERAGE_ELECTR_ENGINE_CONSUMPTION_KEY
                        ):
                            tripElement["electricConsumption"] = int(
                                element.get("value", "0")
                            )
                        if (
                            element.get("key", "")
                            == EUDA_SHORT_TERM_DATA_AVERAGE_FUEL_CONSUMPTION_KEY
                        ):
                            tripElement["fuelConsumption"] = int(
                                element.get("value", "0")
                            )
                        if (
                            element.get("key", "")
                            == EUDA_SHORT_TERM_DATA_AVERAGE_GAS_CONSUMPTION_KEY
                        ):
                            tripElement["gasConsumption"] = int(
                                element.get("value", "0")
                            )
                    # tripElement['tripEnd']=timeStamp
                    if len(tripElement) < 5:
                        if len(tripElement) > 0:
                            self._LOGGER.debug(
                                self.anonymise(
                                    f"tripElement for vehicle {vehicle.vin} has less entries than expected. Only {len(tripElement)}. {tripElement}"
                                )
                            )
                    else:
                        if (
                            self.tripData.get(vehicle.vin, {}).get(
                                tripElement.get("startMileage", 0), {}
                            )
                            == {}
                        ):
                            # add tripElement to self.tripData
                            if tripElement.get("startMileage", 0) > 0:
                                if self.tripData.get(vehicle.vin, {}) == {}:
                                    self.tripData[vehicle.vin] = {}
                                self.tripData[vehicle.vin][
                                    tripElement.get("startMileage", 0)
                                ] = tripElement
                            else:
                                self._LOGGER.warning(
                                    f"tripElement has startMileage=0. {tripElement}"
                                )
                        else:
                            # trip is already in self.tripData
                            if self.tripData.get(vehicle.vin, {}).get(
                                tripElement.get("startMileage", 0), {}
                            ).get("travelTime", 0) < tripElement.get("travelTime", 0):
                                # travelTime in tripElement is bigger than in current element in self.tripData. So we overwrite trip in self.tripData
                                self.tripData[vehicle.vin][
                                    tripElement.get("startMileage", 0)
                                ] = tripElement
                            elif self.tripData.get(vehicle.vin, {}).get(
                                tripElement.get("startMileage", 0), {}
                            ).get("travelTime", 0) == tripElement.get("travelTime", 0):
                                # travelTime in tripElement and self.tripData is equal. Now we compare the timestamp in tripEnd
                                if self.tripData.get(vehicle.vin, {}).get(
                                    tripElement.get("startMileage", 0), {}
                                ).get("tripEnd") > tripElement.get("tripEnd"):
                                    # travelTime is equal, but timestamp of tripElement is older. So we overwrite trip in self.tripData
                                    self.tripData[vehicle.vin][
                                        tripElement.get("startMileage", 0)
                                    ] = tripElement
            return True
        except Exception as e:
            raise PyCupraException(
                f"extractTripsFromRawData() encountered an error. Error: {e}"
            )
        return False

    def readTripStatisticsFile(self, vin: str | None = None) -> bool:
        try:
            if vin is None:
                self._LOGGER.debug(
                    "Reading trip statistics files for all vehicles, if present."
                )
            else:
                self._LOGGER.debug(
                    self.anonymise(
                        f"Reading trip statistics file for vehicle {vin}, if present."
                    )
                )

            for vehicle in self.vehicles:
                if vin is None or vehicle.vin == vin:
                    csvFileName = os.path.join(
                        self._dataBasePath, vehicle.vin + "_drivingData.csv"
                    )
                    if not os.path.exists(csvFileName):
                        self._LOGGER.warning(
                            self.anonymise(
                                f"Could not find trip statistics file {csvFileName}. So starting without trip statistics history."
                            )
                        )
                    else:
                        with open(csvFileName, newline="") as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                data: dict[str, Any] = {}
                                data["startMileage"] = int(row.get("startMileage", "0"))
                                data["fuelConsumption"] = int(
                                    row.get("fuelConsumption", "0")
                                )
                                data["electricConsumption"] = int(
                                    row.get("electricConsumption", "0")
                                )
                                data["gasConsumption"] = int(
                                    row.get("gasConsumption", "0")
                                )
                                data["travelTime"] = int(row.get("travelTime", "0"))
                                data["distance"] = int(row.get("distance", "0"))
                                tripEndString = row.get(
                                    "tripEnd", "2000-01-01 00:00:00+01:00"
                                )
                                data["tripEnd"] = datetime.strptime(
                                    tripEndString, "%Y-%m-%d %H:%M:%S%z"
                                ).astimezone(None)
                                if self.tripData.get(vehicle.vin, None) is None:
                                    self.tripData[vehicle.vin] = {}
                                self.tripData[vehicle.vin][
                                    int(row.get("startMileage", "0"))
                                ] = data
                            csvfile.close()
            return True
        except Exception as error:
            self._LOGGER.error(
                f"Error while reading trip statistics file. Error: {error}."
            )
            raise PyCupraException("Error while trying to read trip statistics file")
        return False

    def writeTripStatisticsFile(self, vin: str | None = None) -> bool:
        try:
            if vin is None:
                self._LOGGER.debug("Writing trip statistics files for all vehicles.")
            else:
                self._LOGGER.debug(
                    self.anonymise(f"Writing trip statistics file for vehicle {vin}.")
                )

            for vehicle in self.vehicles:
                if vin is None or vehicle.vin == vin:
                    csvFileName = os.path.join(
                        self._dataBasePath, vehicle.vin + "_drivingData.csv"
                    )
                    if os.path.exists(csvFileName):
                        os.replace(csvFileName, csvFileName + ".old")

                    with open(csvFileName, "w", newline="") as csvfile:
                        fieldnames = [
                            "rowNo",
                            "tripEnd",
                            "distance",
                            "startMileage",
                            "endMileage",
                            "travelTime",
                            "fuelConsumption",
                            "electricConsumption",
                            "gasConsumption",
                        ]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        rowCounter = 0
                        vehicleTrips = self.tripData.get(vehicle.vin, {})
                        for tripStartMileage in vehicleTrips:
                            trip = self.tripData.get(vehicle.vin, {}).get(
                                tripStartMileage, {}
                            )
                            if trip == {}:
                                self._LOGGER.warning(
                                    f"Did not find trip for start mileage {tripStartMileage}"
                                )
                                return False
                            writer.writerow(
                                {
                                    "rowNo": rowCounter,
                                    "tripEnd": trip.get("tripEnd", ""),
                                    "distance": trip.get("distance", 0),
                                    "startMileage": trip.get("startMileage", 0),
                                    "endMileage": trip.get("startMileage", 0)
                                    + trip.get("distance", 0),
                                    "travelTime": trip.get("travelTime", 0),
                                    "fuelConsumption": trip.get("fuelConsumption", 0),
                                    "electricConsumption": trip.get(
                                        "electricConsumption", 0
                                    ),
                                    "gasConsumption": trip.get("gasConsumption", 0),
                                }
                            )
                            rowCounter = rowCounter + 1
                        csvfile.close()
            return True
        except Exception as error:
            self._LOGGER.error(
                f"Error while writing trip statistics file. Error: {error}."
            )
            raise PyCupraException(
                "Error while trying to write trip statistics to file"
            )
        return False

    async def getData(self, vin: str | None = None) -> bool:
        """ "Reads data like file lists and files for all valid vehicles from the EUDA portal"""
        try:
            if len(self.vehicles) > 0:
                self._LOGGER.debug(
                    self.anonymise(
                        f"In getData, called for vin={vin}. Number of vehicles={len(self.vehicles)}."
                    )
                )
            else:
                self._LOGGER.debug("In getData. Number of vehicles is zero.")

            for vehicle in self.vehicles:
                if vin is None or vehicle.vin == vin:
                    await self.getDataForOneVehicle(vehicle)
            return True
        except Exception as e:
            raise PyCupraException(f"getData() encountered an error. Error: {e}")
        return False

    async def getDataForOneVehicle(self, vehicle: EUDAVehicle) -> bool:
        """ "Reads data like file lists and files for one vehicle from the EUDA portal"""
        try:
            # Reading information for data cluster 'all' (although not using it at the moment)
            await asyncio.sleep(2)
            data = await self.getDatacluster(EUDA_BASE_URL, vehicle.vin, "all")
            if data == {}:
                self._LOGGER.debug(
                    "No data cluster of type 'all' found. Can be ignored, because data cluster 'all' is not necessary."
                )
            else:
                vehicle._states.update(data)
                self._LOGGER.debug(
                    self.anonymise(
                        f"Found data cluster of type 'all'. Name={vehicle._states.get('all', {}).get('Name', '')}"
                    )
                )
                # identifier_all=vehicle._states['all'].get('Identifier','')

            # Reading information for data cluster 'partial'
            identifier_partial = ""
            counter = 0
            while counter < 3 and identifier_partial == "":
                if counter > 0:
                    await asyncio.sleep(2)
                    self._LOGGER.debug(
                        "Trying to read information about data cluster of type 'partial' again."
                    )
                data = await self.getDatacluster(EUDA_BASE_URL, vehicle.vin, "partial")
                if data == {}:
                    self._LOGGER.error("No data cluster of type 'partial' found.")
                else:
                    vehicle._states.update(data)
                    self._LOGGER.debug(
                        self.anonymise(
                            f"Found data cluster of type 'partial'. Name={vehicle._states.get('partial', {}).get('Name', '')}"
                        )
                    )
                    identifier_partial = vehicle._states["partial"].get(
                        "Identifier", ""
                    )
                counter = counter + 1

            if identifier_partial == "":
                self._LOGGER.warning(
                    "Cannot get list of available files of data cluster partial."
                )
                return False

            counter = 0
            fileList: dict = {}
            while counter < 3 and fileList.get("availableDataFiles", []) == []:
                if counter > 0:
                    await asyncio.sleep(2)
                    self._LOGGER.debug("Trying to read list of available files again.")
                fileList = await self.getListOfAvailableFiles(
                    EUDA_BASE_URL, vehicle.vin, identifier_partial, "partial"
                )
                counter = counter + 1
            if fileList.get("availableDataFiles", []) != []:
                for element in fileList.get("availableDataFiles", []):
                    fileName = element.get("name", "")
                    if fileName != "":
                        fileWithPath = os.path.join(self._dataFolder, fileName)
                        processedFileWithPath = os.path.join(
                            self._dataFolderProcessed, fileName
                        )
                        if os.path.isfile(fileWithPath):
                            # self._LOGGER.debug(f'File {fileName} is already present. Not overwriting it.')
                            pass
                        elif os.path.isfile(processedFileWithPath):
                            # self._LOGGER.debug(f"File {fileName} is already present in 'processed' folder. Nothing to do anymore.")
                            pass
                        else:
                            counter = 0
                            fileContent = b""
                            while counter < 3 and len(fileContent) == 0:
                                if counter > 0:
                                    await asyncio.sleep(1)
                                    self._LOGGER.debug(
                                        self.anonymise(
                                            f"Trying to reread file {fileName} again."
                                        )
                                    )
                                fileContent = await self.getOneDatafile(
                                    fileName,
                                    EUDA_BASE_URL,
                                    vehicle.vin,
                                    identifier_partial,
                                    "partial",
                                )
                                counter = counter + 1
                            if len(fileContent) > 0:
                                loop = asyncio.get_running_loop()
                                if fileName.find("_error") > 0:
                                    # There is an error file on the portal
                                    fileWithPath = os.path.join(
                                        self._dataFolderErrorFiles, fileName
                                    )
                                    if not os.path.isfile(fileWithPath):
                                        self._LOGGER.warning(
                                            self.anonymise(
                                                f"Got an error file {fileName} from the portal. Give it a look."
                                            )
                                        )
                                        loop = asyncio.get_running_loop()
                                        await loop.run_in_executor(
                                            None,
                                            self.writeDataFile,
                                            fileWithPath,
                                            fileContent,
                                        )
                                else:
                                    loop = asyncio.get_running_loop()
                                    await loop.run_in_executor(
                                        None,
                                        self.writeDataFile,
                                        fileWithPath,
                                        fileContent,
                                    )
                                self._LOGGER.debug(
                                    self.anonymise(f"Downloaded new file {fileName}.")
                                )
                    else:
                        self._LOGGER.error(
                            "List of available data contains an empty filename."
                        )
            else:
                self._LOGGER.warning(
                    "List of available data is empty. Perhaps you have to wait for data files to become available."
                )
            return True
        except Exception as e:
            raise PyCupraException(
                f"getDataForOneVehicle() encountered an error. Error: {e}"
            )
        return False

    #### Class helpers ####
    @property
    def vehicles(self) -> list:
        """Return list of Vehicle objects."""
        return self._vehicles

    def vehicle(self, vin: str) -> EUDAVehicle | None:
        """Return vehicle object for given vin."""
        return next(
            (
                vehicle
                for vehicle in self.vehicles
                if vehicle.unique_id.lower() == vin.lower()
            ),
            None,
        )

    # def hash_spin(self, challenge, spin) -> str:
    #    """Convert SPIN and challenge to hash."""
    #    spinArray = bytearray.fromhex(spin);
    #    byteChallenge = bytearray.fromhex(challenge);
    #    spinArray.extend(byteChallenge)
    #    return hashlib.sha512(spinArray).hexdigest()

    def addToAnonymisationDict(self, keyword: str, replacement: str) -> None:
        self._anonymisationDict[keyword] = replacement

    def addToAnonymisationKeys(self, keyword: str) -> None:
        self._anonymisationKeys.add(keyword)

    def anonymise(self, inObj) -> Any:
        if self._session_anonymise:
            if isinstance(inObj, str):
                for key, value in self._anonymisationDict.items():
                    inObj = inObj.replace(key, value)
            elif isinstance(inObj, dict):
                for elem in inObj:
                    if elem in self._anonymisationKeys:
                        inObj[elem] = "[ANONYMISED]"
                    else:
                        inObj[elem] = self.anonymise(inObj[elem])
            elif isinstance(inObj, list):
                for i in range(len(inObj)):
                    inObj[i] = self.anonymise(inObj[i])
        return inObj


# End of class definition for EUDAConnection


def GetVINFromFileName(fileName: str) -> str:
    posJson = fileName.find(".json")
    posZip = fileName.find(".zip")
    posSeparator = fileName.find("_")
    if posSeparator > 0:
        if posZip > posJson:
            # The file is a zip file
            if fileName[:2] == "20":  # Filename has timestamp before vin
                if posZip > posSeparator + 1:
                    return fileName[posSeparator + 1 : posZip]
            else:
                # Filename has vin before timestamp
                return fileName[:posSeparator]
        else:
            # The file is a json file
            if fileName[:2] == "20":  # Filename has timestamp before vin
                if posJson > posSeparator + 1:
                    return fileName[posSeparator + 1 : posJson]
            else:
                # Filename has vin before timestamp
                return fileName[:posSeparator]
    return ""


def GetTimeStampFromFileName(fileName: str) -> datetime:
    try:
        posJson = fileName.find(".json")
        posZip = fileName.find(".zip")
        posSeparator = fileName.find("_")
        if posZip > posJson:
            # The file is a zip file
            if posSeparator > 0 and posZip > posSeparator + 2:
                if fileName[:2] == "20":  # Filename has timestamp before vin
                    timeStampString = fileName[0:posSeparator]
                    # The timestamps are utc timestamps
                    return (
                        datetime.strptime(timeStampString + "Z", "%Y%m%d%H%M%SZ")
                        .replace(tzinfo=timezone.utc)
                        .astimezone(None)
                    )
                # Filename has vin before timestamp
                timeStampString = fileName[posSeparator + 1 : posZip]
                # The timestamps are utc timestamps
                return (
                    datetime.strptime(timeStampString + "Z", "%Y%m%d%H%M%SZ")
                    .replace(tzinfo=timezone.utc)
                    .astimezone(None)
                )
        else:
            # The file is a json file
            if posSeparator > 0 and posJson > posSeparator + 2:
                if fileName[:2] == "20":  # Filename has timestamp before vin
                    timeStampString = fileName[0:posSeparator]
                    # The timestamps are utc timestamps
                    return (
                        datetime.strptime(timeStampString + "Z", "%Y%m%d%H%M%SZ")
                        .replace(tzinfo=timezone.utc)
                        .astimezone(None)
                    )
                # Filename has vin before timestamp
                timeStampString = fileName[posSeparator + 1 : posJson]
                # The timestamps are utc timestamps
                return (
                    datetime.strptime(timeStampString + "Z", "%Y%m%d%H%M%SZ")
                    .replace(tzinfo=timezone.utc)
                    .astimezone(None)
                )
    except Exception:
        _LOGGER.error(f"Error in getTimeStampFromFileName for file name '{fileName}'")
    return datetime(2000, 1, 1).replace(tzinfo=timezone.utc).astimezone(None)


async def main():
    """Main method."""
    if "-v" in argv:
        logging.basicConfig(level=logging.INFO)
    elif "-vv" in argv:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    async with ClientSession(headers={"Connection": "keep-alive"}) as session:
        connection = EUDAConnection(
            session, brand="cupra", username="xxx", password="yyy", fulldebug=True
        )
        if await connection.doLogin():
            if await connection.getVehicles():
                for vehicle in connection.vehicles:
                    print(f"Vehicle id: {vehicle}")
                    print("Supported sensors:")
                    for instrument in vehicle.dashboard().instruments:
                        print(
                            f" - {instrument.name} (domain:{instrument.component}) - {instrument.str_state}"
                        )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
