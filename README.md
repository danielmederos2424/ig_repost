# Instagram Reels Reposter

## Overview

This Python script automates the process of reposting Instagram Reels sent via Direct Messages (DMs) to your account's feed. It logs into Instagram, checks DMs for reels shared by specific users, downloads the reels, and reposts them with a custom caption and hashtags. It is designed to run continuously, logging in every two minutes, checking for new content, and posting if any new reels are found.

The script uses `instagrapi` for interacting with Instagram and relies on `requests` to download media content. This can be particularly useful for meme pages, content aggregation accounts, or other users who want to automatically repost reels from certain sources.

## Features

- **Automatic Login**: The script logs into Instagram at the start of each check to ensure an active session.
- **Custom Caption Support**: You can define your own caption, including hashtags, to be added to each reposted reel.
- **User-Specified Accounts**: Reels are reposted only if sent from a list of specified Instagram usernames.
- **State Persistence**: The script saves the timestamp of the last reposted reel for each target user, allowing it to pick up where it left off even after restarts.
- **Logging**: Detailed logging tracks all major actions, including login attempts, download and upload status, and errors.

## Setup

### Prerequisites

- Python 3.7+
- `instagrapi` and `requests` packages

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

1. **Update Account Credentials**: Replace `self.username` and `self.password` with your Instagram credentials in the script.
2. **Specify Target Usernames**: Add the usernames of the accounts whose reels you want to monitor to `self.target_usernames`.
3. **Customize Caption**: Modify `self.custom_caption` to define the caption that will accompany each repost. This can include hashtags or other information relevant to your reposting strategy.

### Run the Script

To start the reposting bot, run the script:

```bash
python3 main.py
```

> **Note:** Ensure that the script has permission to write logs and temporary files in its directory.

### Logs and State Management

- **Logs**: Log files are stored in the `logs` folder. Each log file records actions, such as successful logins, downloads, uploads, and errors.
- **State File**: The script uses `reposter_state.pkl` to track the last reposted reel from each target account. This file ensures that the script does not repost the same reel multiple times and picks up where it left off if interrupted.

## How It Works

1. **Login**: Every two minutes, the script logs into Instagram to initiate a new session.
2. **DM Monitoring**: It fetches recent messages from DMs and checks for any reels sent by the target usernames.
3. **Download and Repost**: If new reels are found, the script downloads them, applies the custom caption, and reposts them to the account's feed.
4. **Cleanup**: After reposting, temporary files are deleted to conserve storage space.

## Important Notes

- **Instagram API Limitations**: Frequent logins and interactions with Instagram's API may risk temporary account restrictions. Adjust the interval if you encounter issues.
- **Handling Interruptions**: The script is designed to handle graceful shutdowns, preserving state data and cleaning up temporary files.
- **Rate Limits**: Instagram has strict rate limits on actions like logging in, sending messages, and posting. Avoid frequent, high-volume reposting to minimize the risk of being flagged by Instagram.

### Handling Errors and Logs

If any error occurs, the script logs the error details and attempts to continue. You can check the logs in the `logs` folder to troubleshoot issues, such as failed logins, network issues, or Instagram rate limits.

## License

This project is open-source and available for modification and personal use. However, keep in mind that use of automated scripts to interact with Instagram may violate their terms of service. Use this tool responsibly and at your own risk.
