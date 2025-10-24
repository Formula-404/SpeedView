# **SpeedView**

Setiap balapan **Formula 1** bukan hanya tentang *20 mobil yang berputar di suatu lintasan*.  
Tapi ini tentang kombinasi **pembalap yang memacu batasan**, **tim pemenang adalah tim yang bermain strategi**, dan detail kecil seperti **cuaca** atau **timing pit stop** yang bisa menentukan hasil akhir.

---

**SpeedView** hadir untuk melihat lebih dekat detail-detail itu.  
Tujuannya adalah mengubah **data balapan yang tadinya monoton dan teknis** menjadi **hub interaktif** tempat penggemar, mahasiswa, dan peneliti bisa:

- Menjelajahi balapan lewat ***meetings, sessions, drivers, dan circuits***
- Menganalisis performa lewat **lap times, pengaruh cuaca, dan pit strategies**
- Mempelajari sisi **teknis dari olahraga ini** (*cars, teams, telemetry*)


## Deployment
<p align="center">
    <img src="static/image/docs/Banner.png" alt="SpeedView Live" width="600"/>
    <a href="https://helven-marcia-speedview.pbp.cs.ui.ac.id" target="_blank">
        <br/>
        <b>SpeedView</b>
        <br/>
    </a>
    <sub>Hosted on Pacil Web Service</sub>
</p>

## Contributor
<table>
    <tr>
        <td align="center">
            <a href="https://github.com/helvenix">
                <img src="https://avatars.githubusercontent.com/u/109453997?v=4" width="80px;" alt="Helven Marica"/>
                <br /><sub><b>Helven Marcia</b></sub>
            </a>
        </td>
        <td align="center">
            <a href="https://github.com/haekalhdn">
                <img src="https://avatars.githubusercontent.com/u/178357458?v=4" width="80px;" alt="Haekal Handrian"/>
                <br /><sub><b>Haekal Handrian</b></sub>
            </a>
        </td>
        <td align="center">
            <a href="https://github.com/puut12">
                <img src="https://avatars.githubusercontent.com/u/198161335?v=4" width="80px;" alt="Putri Hamidah Riyanto"/>
                <br /><sub><b>Putri Hamidah Riyanto</b></sub>
            </a>
        </td>
        <td align="center">
            <a href="https://github.com/nail-nail">
                <img src="https://avatars.githubusercontent.com/u/198184000?v=4" width="80px;" alt="Naila Khadijah"/>
                <br /><sub><b>Naila Khadijah</b></sub>
            </a>
        </td>
        <td align="center">
            <a href="https://github.com/lucidd2712">
                <img src="https://avatars.githubusercontent.com/u/198191346?v=4" width="80px;" alt="Gilang Adjie Saputra"/>
                <br /><sub><b>Gilang Adjie Saputra</b></sub>
            </a>
        </td>
    </tr>
</table>

## Module Overview
<table>
  <tr>
    <th style="width:180px; text-align:left;">Module</th>
    <th style="text-align:left;">Purpose</th>
    <th style="text-align:left;">Developer</th>
  </tr>
  <tr>
    <td><b>User</b></td>
    <td>Authentication, user profiles, and role permissions</td>
    <td>Haekal</td>
  </tr>
  <tr>
    <td><b>Driver</b></td>
    <td>Stores driver details, nationality, and racing statistics</td>
    <td>Gilang</td>
  </tr>
  <tr>
    <td><b>Circuit</b></td>
    <td>Metadata about circuits (name, location, length, turns, layout)</td>
    <td>Putri</td>
  </tr>
  <tr>
    <td><b>Meeting</b></td>
    <td>Represents a Grand Prix weekend (e.g., Monaco GP 2025)</td>
    <td>Putri</td>
  </tr>
  <tr>
    <td><b>Session</b></td>
    <td>Practice sessions, Qualifying, Sprint, and Race data</td>
    <td>Putri</td>
  </tr>
  <tr>
    <td><b>Weather</b></td>
    <td>Environmental conditions (track temperature, rain, wind, humidity)</td>
    <td>Putri</td>
  </tr>
  <tr>
    <td><b>Team</b></td>
    <td>Constructor details, linked with drivers and cars</td>
    <td>Helven</td>
  </tr>
  <tr>
    <td><b>Car</b></td>
    <td>Technical specifications of cars (engine, chassis, season entries)</td>
    <td>Naila</td>
  </tr>
  <tr>
    <td><b>Laps</b></td>
    <td>Lap-by-lap performance data, including timing, sectors, and telemetry</td>
    <td>Gilang</td>
  </tr>
  <tr>
    <td><b>Pit</b></td>
    <td>Pit stop strategies, tire changes, and related time losses</td>
    <td>Gilang</td>
  </tr>
  <tr>
    <td><b>Comparison</b></td>
    <td>Comparison session to compare Driver, Team, Car, Circuit with statistical view</td>
    <td>Helven</td>
  </tr>
</table>

## **User Roles**

### 🧭 **Guest**
- Hanya bisa mengakses halaman dengan mode *read-only*

### 👤 **Login User**
- Bisa **membuat dan menyimpan sesi perbandingan (comparison sessions)**
- Dapat **membagikan sesi** dengan pengguna lain

### 🛠️ **Admin**
- Dapat **mengedit data wiki tertentu**
- Bisa **memoderasi forum** (menghapus postingan)
- Memiliki **alat dan izin manajemen tambahan**



## Initial Dataset Source Credit
<p align="left">
  <a href="https://openf1.org"><img src="https://img.shields.io/badge/Data-OpenF1-red?style=flat-square&logo=fastapi&logoColor=white" alt="OpenF1"/></a>
  <a href="https://en.wikipedia.org/wiki/List_of_Formula_One_circuits"><img src="https://img.shields.io/badge/Data-Wikipedia-blue?style=flat-square&logo=wikipedia&logoColor=white" alt="Wikipedia"/></a>
  <a href="https://www.formula1.com"><img src="https://img.shields.io/badge/Data-formula1-red?style=flat-square&logo=f1&logoColor=white" alt="Formula 1"/></a>
</p>


## Getting Started

### 1. Clone this repo
```bash
git clone https://github.com/Formula-404/SpeedView.git
cd SpeedView
```

### 2. Create a virtual environment
**Windows (PowerShell)**
```powershell
python -m venv env
.venv\Scripts\Activate
```
**macOS / Linux (bash/zsh)**
```bash
python3 -m venv env
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
create a file named .env in the project root and paste this
```dotenv
PRODUCTION=False
```

### 5. Apply database migrations
```bash
python manage.py migrate
```

### 6. Run the development server
```bash
python manage.py runserver
```

## Others
<p align="left">
    <a href="https://www.figma.com/files/team/1555462377026209078/project/463049743/SpeedView?fuid=1485588854028450044">
        <img src="https://img.shields.io/badge/Figma-Design%20Mockups-purple?style=for-the-badge&logo=figma&logoColor=white" alt="Figma Project"/>
    </a>
</p>