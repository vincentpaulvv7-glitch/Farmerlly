# Farmerlly

Farmerlly is a beginner-friendly, multilingual farming dashboard built with Streamlit. Its interface supports English, Tamil, Telugu, Malayalam, Hindi, and Kannada. It stores a farm profile and crop records in SQLite, retrieves live weather from Open-Meteo, and provides crop management, farming roadmaps, notifications, and water guidance.

## Requirements

- Python 3.12 (the pinned dependencies are checked with Python 3.12)
- pip

## Create a virtual environment and install dependencies

From the project folder, run these commands in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, you can install using the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

To start the app:

```powershell
streamlit run app.py
```

## Starter structure

```text
Farmerlly/
├── app.py                 # Streamlit dashboard and page routing
├── .streamlit/
│   └── config.toml        # Native Streamlit light and dark themes
├── farmerlly/
│   ├── __init__.py        # Marks farmerlly as a Python package
│   ├── crop_catalog.py    # Extensible crop, variety, and growth-stage catalog
│   ├── crop_coefficients.json # Source-linked FAO-56 crop-stage Kc values
│   ├── crop_ui.py         # Crop registration, details, and progress editing
│   ├── database.py        # SQLite helpers for farmer profiles and crop records
│   ├── notifications.py   # Forecast, due-task, and crop-stage alerts with read state
│   ├── profile_ui.py      # Registration, profile editing, and input validation
│   ├── roadmap.py         # Crop and forecast based task roadmap
│   └── water_advisor.py   # Crop water guidance and FAO-56 ETc estimate
├── modules/
│   ├── __init__.py        # Marks modules as an integration package
│   └── weather.py         # Open-Meteo geocoding, current weather, forecast, and alerts
├── requirements.txt       # Python dependencies for the project
├── README.md              # Project overview and setup instructions
└── .gitignore             # Excludes environments, secrets, local databases, and cache files
```


The dashboard sections include weather, crops, a Smart Farming Roadmap, notifications, and a Water Requirement Advisor. The overview's notification center uses live forecast alerts, incomplete roadmap tasks due today, and configured crop-stage activities; active alerts have stable identifiers and read states are stored in SQLite to prevent repeated unread notices. Weather alerts are forecast-based planning cues, not official warnings. A farmer can register and edit their name, preferred language, location, farm size, soil type, water sources, and crops. The profile, individually tracked crop records, selected irrigation method per crop, roadmap task completion states, and notification read states are stored in the local `farmerlly.db` SQLite file, which is excluded from Git. Crop records track planting date, optional variety, growth stage, irrigation method, and manually updated progress. The roadmap lets a farmer select a crop and planning duration, generates today's and weekly checklists, and uses the crop's current stage and available Open-Meteo forecast to show stage activities and weather precautions. Completed task states are saved locally. Forecast cues are not official warnings, and actions that vary by variety, season, soil, and location are flagged for local verification. No pesticide, fertilizer dose, or yield promise is generated.

## Deploy on Streamlit Community Cloud

The current project is suitable for a **single-farm demonstration**, not a public multi-farmer service. See [Application and data limitations](#application-and-data-limitations) before sharing a deployment.

### 1. Prepare the GitHub repository

This workspace does not currently contain a Git repository. Create a private GitHub repository, then from this project folder run:

```powershell
git init
git add app.py farmerlly modules .streamlit/config.toml requirements.txt README.md .gitignore
git status --short
```

Review the staged files before committing. `.env`, `.venv`, and `farmerlly.db` must not appear. Do not force-add them. Then connect your private repository and push the reviewed source:

```powershell
git commit -m "Prepare Farmerlly for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_PRIVATE_REPOSITORY.git
git push -u origin main
```

If you already have a repository, skip `git init` and add only the changed project files. Community Cloud needs access to the repository; the deploying GitHub account must have repository admin permission.

### 2. Create the Community Cloud app

1. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub and grant it access to the private repository.
2. Select **Create app** and **Yup, I have an app**.
3. Select your repository, the `main` branch, and `app.py` as the app file.
4. Open **Advanced settings**, choose **Python 3.12**, and continue without adding API secrets.
5. Select **Save** and **Deploy**. Review the build log if the app does not start.
6. In **App settings → Sharing**, confirm that the app is private and invite only the intended demo viewers. Community Cloud apps inherit repository visibility; a private repository defaults to a private app. A workspace can have only one private Community Cloud app. See [app sharing and privacy](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app).

Community Cloud reads the root `requirements.txt` and `.streamlit/config.toml`. Its current default Python is 3.12; this project's dependency pins were checked with Python 3.12. See Streamlit's [deployment steps](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

### 3. API credentials

Open-Meteo weather and the source-linked crop coefficient configuration do not require API keys. Do not add unused secrets to the deployment.

### 4. Confirm the deployed app

Open the app URL and follow the [demo walkthrough](#demo-walkthrough) below using fictional details. Check the Community Cloud app logs if startup fails. The app can also be redeployed automatically after changes are pushed to the selected branch.

## Demo walkthrough

Use fictional profile details only. Do not enter a real farmer's name, contact details, or private farm information into a shared demonstration app.

1. Open **Farmer profile** and register a clearly fictional farmer, a demonstration location, soil/water choices, and crops such as rice and tomato.
2. Switch among English, Tamil, Telugu, Malayalam, Hindi, and Kannada in the sidebar.
3. Open **Overview** and review current weather and forecast. Weather is live Open-Meteo data; if the location/API is unavailable, the app reports the error instead of showing sample weather.
4. In **My crops**, add at least two crop records with planting dates, varieties where available, and growth stages. Update crop progress to demonstrate editing.
5. Open **Smart Farming Roadmap**, choose a crop and planning duration, then mark a task complete.
6. Open **Water advisory**, choose an irrigation method, and review the forecast context and any available ETc estimate. It does not invent a fixed irrigation volume.

## Application and data limitations

- **Single shared profile:** SQLite stores the farmer profile in a single row and crop/roadmap data in the same local database. There is no login, user separation, or access control. Anyone who can use one shared deployment could see or change the same farm records. Do not deploy this version as a public service for real farmers.
- **Cloud storage is not durable:** Community Cloud does not guarantee persistence of files written by a running app. Its local `farmerlly.db` may be deleted, including after a restart or rebuild. Do not treat it as a backup or permanent production database. See Streamlit's [local SQLite and storage documentation](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data).
- **Before real use:** add authentication and per-user records, migrate farm data to a managed persistent database, and plan backups and access controls. SQLite in the current app is for local development and single-farm demos.
- **External services:** weather results depend on the upstream service, network availability, quotas, and returned data.
- **Agricultural guidance:** forecast advisories are not official alerts. Crop, water, and roadmap guidance is general and may need local KVK or agriculture-department verification.
- **Community Cloud may hibernate:** apps with no traffic for 12 hours go to sleep and may take time to wake. See [app management and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).

Add crop definitions and crop-specific growth stages in `farmerlly/crop_catalog.py`; variety lists can include a source URL. Roadmap guidance links to [TNAU rice irrigation](https://agritech.tnau.ac.in/agriculture/agri_irrigationmgt_cereals_rice.html), [TNAU rice nutrient management](https://agritech.tnau.ac.in/expert_system/paddy/nutrientmanagement.html), [TNAU tomato cultivation](https://agritech.tnau.ac.in/horticulture/agri_seasonandvarieties_tomato.html), [TNAU tomato water management](https://agritech.tnau.ac.in/org_farm/orgfarm_tomato_water.html), and [TNAU banana cultivation and irrigation](https://agritech.tnau.ac.in/horticulture/horti_fruits_banana.html). These are general references; consult the local KVK or agriculture department for field-specific decisions. Starter variety choices for rice, tomato, and banana link to [TNAU rice varieties](https://agritech.tnau.ac.in/agriculture/agri_cropproduction_cereals_rice_season.html), [TNAU tomato varieties](https://agritech.tnau.ac.in/horticulture/agri_seasonandvarieties_tomato.html), and [TNAU banana varieties](https://agritech.tnau.ac.in/horticulture/horti_fruits_banana.html); they are not location-specific recommendations.

The Water Requirement Advisor uses Open-Meteo forecast rainfall and daily ET0, the selected crop and growth stage, saved soil type, and irrigation method. For configured rice, tomato, banana, maize, wheat, cotton, sugarcane, groundnut, millet, and pulses stages, it calculates daily and seven-day indicative ETc from matching daily values using ETc = Kc * ET0. Crop-stage coefficients and their source notes are stored in farmerlly/crop_coefficients.json. These are FAO-56 planning values rather than local calibrations; climate, crop-stage duration, canopy, and wetting adjustments may change actual Kc. The rice nursery value is the FAO-56 initial paddy-rice coefficient (Kc 1.05), which assumes 0.10 to 0.20 m standing water and may not fit a dry or mat nursery. Forecast rainfall is shown separately and is not assumed to be effective rainfall. The advisor does not calculate an irrigation volume because effective rainfall, soil-water storage, crop condition, and irrigation-system performance are not sufficiently known. It links FAO-56 crop evapotranspiration (https://www.fao.org/4/X0490E/x0490e0b.htm), Open-Meteo ET0 documentation (https://open-meteo.com/en/docs), and relevant TNAU water-management guidance. Weather errors do not fall back to sample weather. Weather alerts are forecast-based advisories, not official emergency warnings. SQLite is included with Python standard library.
