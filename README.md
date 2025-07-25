# apple-photos-aura-frame-syncer

Automatically sync Apple Photos albums to your Aura smart frame.

## Setup

### 1. Create and activate the Anaconda environment
```sh
conda env create -f environment.yml
conda activate pple-photos-aura-frame-syncer
```

### 2. Set up .env
```sh
# Copy the example environment file
cp .env.example .env

# Then edit .env with your actual values:
# - AURA_EMAIL: Your Aura frame account email
# - AURA_PASSWORD: Your Aura frame account password
# - SYNC_ALBUMS: Comma-separated list of Apple Photos albums to sync
# - GITHUB_TOKEN: A GitHub personal access token for tracking sync state
# - SYNC_GIST_ID: ID of a GitHub Gist to store sync state
```

### 3. Run the scheduler
```sh
python scheduler.py
```

The scheduler will:
1. Immediately sync the configured albums on startup
2. Continue syncing every 30 minutes
3. Track sync state in a GitHub Gist to avoid re-uploading the same photos