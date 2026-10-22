# Home Assistant Add-on: GameDock

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

_GameDock serves your Nintendo Switch game library to the console over your home network._

## About

🎮 Library with covers, search and filters: games, updates and DLC you have and the ones you are missing

🔌 Connect page with the address to type on the console for Tinfoil, Sphaira and CyberFoil

🗂️ Organizes, verifies and compresses the files automatically

🔔 Notifications through ntfy, Telegram or Discord for new games, available updates and DLC, and failed verifications

👥 Users with their own permissions

🌎 English, Portuguese and Spanish

## Setup

1. Put your games in a folder under `/media` or `/share`, for example `/media/games`.
2. Open the web UI and go to **Admin → Settings → Users** to create an administrator. Until the first administrator exists, anyone on your network can open the admin pages.
3. In **Admin → Settings → Library**, add your games folder and remove the default `/games` folder.

## Data

The database and settings are kept in the add-on configuration folder, and the downloaded game catalogue and logs in the add-on data folder, so both are included in Home Assistant backups.

https://github.com/guslma/GameDock

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-no-red.svg
[armv7-shield]: https://img.shields.io/badge/armv7-no-red.svg
[i386-shield]: https://img.shields.io/badge/i386-no-red.svg
