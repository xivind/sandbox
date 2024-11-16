# About
Bla bla, content and short description




# Blinkt (new picture)
This scipt uses the [ledstrip](https://shop.pimoroni.com/products/blinkt) from [Pimoroni](https://shop.pimoroni.com/) to display system status. To make it run in the background, create a service file with the content below and place it in `/etc/systemd/system` Use `sudo systemctl enable <name of service file>` to make it run on system startup
>`[Unit]`  
`Description=Control status LEDs for RPI4s`  
`After=network.target`  
`[Service]`  
`ExecStart=/usr/bin/python3 -u <full path to python script>`  
`rpi4-statusleds.py`  
`WorkingDirectory=<full path to directory that contains the python script>`  
`StandardOutput=inherit`  
`StandardError=inherit`  
`Restart=always`  
`User=<name of user to run the script>`  
`[Install]`  
`WantedBy=multi-user.target`  

The Pimoroni Blinkt in use at a Raspberry Pi4b with the [Argon40 Argon ONE M.2 Case](https://www.argon40.com/argon-one-m-2-case-for-raspberry-pi-4.html)
![Pimoroni Blinkt](/blinkt/IMG_20210722_000358.jpg)
