# SpeedView

Every Formula 1 race is more than just 20 cars circling a track.  
It’s a blend of drivers pushing limits, teams playing strategy, and tiny details, like weather or pit timing that decide the outcome.  

**SpeedView** was created to capture those details.  
Its purpose is to turn raw, technical race data into an interactive hub where fans, students, and researchers can:  

- Explore races through **meetings, sessions, drivers, and circuits**  
- Analyze performance with **lap times, weather effects, and pit strategies**  
- Study the **technical side of the sport** (cars, teams, telemetry)  

## Deployment
<p align="center">
    <a href="https://helven-marcia-speedview.pbp.cs.ui.ac.id" target="_blank">
        <img src="static/image/docs/Banner.png" alt="SpeedView Live" width="600"/>
        <br/>
        <b>SpeedView</b>
        <br/>
        <sub>Hosted on PWS | Production Build</sub>
    </a>
</p>

## Contributor
<table>
    <tr>
        <td align="center">
            <a href="https://github.com/helvenix">
                <img src="https://avatars.githubusercontent.com/u/109453997?v=4"           width="80px;" alt="Helven Marica"/>
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
            <a href="https://github.com/nailnail">
                <img src="https://avatars.githubusercontent.com/u/30210192?v=4" width="80px;" alt="Naila Khadijah"/>
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
  </tr>
  <tr>
    <td><b>User</b></td>
    <td>Authentication, user profiles, and role permissions</td>
  </tr>
  <tr>
    <td><b>Driver</b></td>
    <td>Stores driver details, nationality, and racing statistics</td>
  </tr>
  <tr>
    <td><b>Circuit</b></td>
    <td>Metadata about circuits (name, location, length, turns, layout)</td>
  </tr>
  <tr>
    <td><b>Meeting</b></td>
    <td>Represents a Grand Prix weekend (e.g., Monaco GP 2025)</td>
  </tr>
  <tr>
    <td><b>Session</b></td>
    <td>Practice sessions, Qualifying, Sprint, and Race data</td>
  </tr>
  <tr>
    <td><b>Weather</b></td>
    <td>Environmental conditions (track temperature, rain, wind, humidity)</td>
  </tr>
  <tr>
    <td><b>Team</b></td>
    <td>Constructor details, linked with drivers and cars</td>
  </tr>
  <tr>
    <td><b>Car</b></td>
    <td>Technical specifications of cars (engine, chassis, season entries)</td>
  </tr>
  <tr>
    <td><b>Laps</b></td>
    <td>Lap-by-lap performance data, including timing, sectors, and telemetry</td>
  </tr>
  <tr>
    <td><b>Pit</b></td>
    <td>Pit stop strategies, tire changes, and related time losses</td>
  </tr>
  <tr>
    <td><b>Comparison</b></td>
    <td>Comparison session to compare Driver, Team, Car, Circuit</td>
  </tr>
</table>

## User Roles  

- **Guest** → Can only access read-only pages
- **Login User** →  
  - Create and save comparison sessions  
  - Share sessions with others  
  - Start forum content (articles, discussions, fan meetings)  
  - Comment and interact with forum content  
- **Admin** →  
  - Edit certain wiki data
  - Moderate forum discussions (delete posts/comments)  
  - Additional management tools and permissions  


## Initial Dataset Source Credit
<p align="left">
  <a href="https://openf1.org"><img src="https://img.shields.io/badge/Data-OpenF1-red?style=flat-square&logo=fastapi&logoColor=white" alt="OpenF1"/></a>
  <a href="https://www.wikipedia.org/"><img src="https://img.shields.io/badge/Data-Wikipedia-blue?style=flat-square&logo=wikipedia&logoColor=white" alt="Wikipedia"/></a>
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
    <a href="https://figma.com/">
        <img src="https://img.shields.io/badge/Figma-Design%20Mockups-purple?style=for-the-badge&logo=figma&logoColor=white" alt="Figma Project"/>
    </a>
</p>