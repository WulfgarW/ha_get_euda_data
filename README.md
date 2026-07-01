# Get EUDA data - A Home Assistant custom component using the get_euda_data library to add integration to read data for your car from the EU Data Act portal of Volkswagen group 

This integration for Home Assistant will fetch data from the EU Data Act servers related to your car. It supports the brands Audi, Cupra, Seat, Skoda and Volkswagen (only passenger cars).

## This is integration is based on [PyCupra](https://github.com/WulfgarW/homeassistant-pycupra), but now solely using the EU Data Act portal as data source.

### Supported setups
This integration will only work for your car(s), if you have done the necessary preparation steps (see section 'Preparations to get EU Data Act data for your vehicle'). 

## Range of functions
- It depends on your vehicle model, which home assistant entities become available for your vehicle. And it depends on, for which fields there is a definition present in the Get_EUDA_Data code. So if you see fields in your EUDA files, that you want to have as entities in home assistant, open an issue (https://github.com/WulfgarW/ha_get_euda_data/issues). New versions of Get_EUDA_Data can make more entities available.

- And you should see an entity 'Other fields found'. The value shown for this entity is the number of fields found in your current EUDA file, for which there is no entity defined at the moment. And if you open the details for the 'Other fields found' entity, you see the name of these fields and the current value (as text) in the entity attributes.
- If you see 'interesting' fields in the attributes of the 'Other fields found' entity, reload your device (via Settings>Devices&Services>Get_EUDA_Data, click on the three vertical points right from the cogwheel and chosse 'Reload').
- It can happen, that a field, that was available in the current EUDA file when you reloaded you Get_EUDA_Data device is not always present in other EUDA files for your vehicle. E.g. some fields are only available, while your vehicle is charging. So don't be surprised, when you see 'Unavailable' for some entities. It is possible, that you find fields like "state_sunroof_motor_hood_1" in your EUDA files, although your vehicle has no sunroof. The field value "0" means "unsupported", the field value "1" means "invalid". For such fields, Get_EUDA_Data will treat the values "0" and "1" as if the field is not available.
- In contrast to PyCupra and similar integrations, that communicated with the brands API, that the official mobile phone apps of your brand are using, Get_EUDA_Data can only read data for your vehicle, it cannot change any vehicle setting.

### How to use the driving data sum files
- In the 'euda_data' folder (should normally be a subfolder of the <config dir> folder of HA), you find the files <VIN>_drivingData.csv (and an .old file for it). Get_EUDA_Data uses this file, to provide you with a history of the driving data. You can copy the file for further data analysis to another location, but do not delete it from the 'euda_data' folder and do not edit it accidently.

### Files in the euda_data/euda_files folder
- Get_EUDA_Data collects the files downloaded from the EUDA portal in the folder 'euda_data/euda_files' and its in subfolders. So it preserves a history of the EUDA files for your vehicle(s). 
- In order to prevent, that number of files in the 'processed' folder gets confusingly large, files with a timestamp older than 10 days get moved to 'archive' folder and added to an archive file there.
- The archive files are not very big. But if you want to save disk space, you can delete older archive files. Please don't delete the archive files for the current month and the month before.


## Preparations to get EU Data Act data for your vehicle

### Login the EU Data Act portal
- Open https://eu-data-act.drivesomethinggreater.com in your browser.
- Click on the green "Log in" button.
- Now choose your brand and click "Login" and then "Continue" on the follwoing page.
- You will be redirected to the login page of Seat (yes also for Cupra users) and login there.

### Choose your vehicle, allow access and set up a customised data request
- After a successful login, you will be redirected back to the EU Data Act portal.
- You see a list of your connected vehicles (only one for most of you).
- Click on "Vehicle details" for your vehicle.
- You will be asked to allow "My Data Portal" to access. (I don't remember. Perhaps this question already comes during the login.)
- You should see a section "Get customised data" where you can click on "Request customised data".
- Now set up your request. Choose all data clusters, an interval of 15 minutes, the request should stay for unlimited time, and you can name it as you like (e.g. 'All data 15mins')
- If that worked, you can log off.

### Wait for data files to get available
- It will take several hours (sometimes even more than 24 hours), until the first data get available. And there will be no notification.
- So login from time to time, choose your vehicle and click on vehicle details to look, if there are files ready for download.
- If you see one or several files, then it is time to install and initialise the Get_EUDA_Data integration in HA.
- Optional: You can download at least one of the files to learn, how the data are provided. The files on the EUDA portal are normally zipped files containing just one text file. Unzip a downloaded zip file and open the json file from this zip file with a text editor to see the structure of the EUDA files.


## Installation

### Installation with HACS
If you have HACS (Home Assistant Community Store) installed, go to the tab HACS on the Home Assistant UI.  Click on the three vertical points on the top and right of the screen and choose 'Custom repositories'. 
Enter 'https://github.com/WulfgarW/ha_get_euda_data' as repository and choose the type 'integration' and click on 'Add'. When HACS has loaded the repository information, leave this submenu with cancel. Now you can enter 'euda' in the search field and should find 'Get EUDA Data'. Click on the three vertical points and choose 'Download'.
After that, you can go to Settings>Devices&Services, choose 'Add integration' and search for 'Get_EUDA_Data'.

### Manual installation
Clone or copy the repository and copy the folder 'ha_get_euda_data/custom_components/get_euda_data' into '<config dir>/custom_components'

## Configure

### Entering credentials and choosing vehicle
When you are adding a Get_EUDA_Data device, you are first asked to choose the vehicles brand and to enter your username and your password for the EUDA Data Act portal.
When the login was successful, you see the vehicles available under your account. Choose one of them.
(If you have several vehicles and want to use Get_EUDA_Data for more than one of them, you have to set up one Get_EUDA_Data device per vehicle.)

### Configuration options
The integration options can be changed after setup by clicking on the "CONFIGURE" text on the integration.
The options available are:

* **Poll frequency** The interval (in seconds) that the servers are polled for updated data. Please don't use values below 300 seconds, better 600 or 900 seconds.
 
* **Full API debug logging** Enable full debug logging. This will print the full respones from API to homeassistant.log. Only enable for troubleshooting since it will generate a lot of logs.

* **Resources to monitor** Select which resources you wish to monitor for the vehicle.

## Enable debug logging
For comprehensive debug logging you can add this to your `<config dir>/configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    get_euda_data: debug
    custom_components.get_euda_data: debug
 ```
## Further help or contributions
For questions, further help or contributions you can join the (V.A.G. Connected Cars) Discord server at https://discord.gg/826X9jEtCh
