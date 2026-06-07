# Summer-Party-Four-Cuts

Four cuts for Summer Party MPI-CBS 2026

![overview](asset\overview.png)

## Installation

UV [https://docs.astral.sh/uv/getting-started/installation/#standalone-installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)

Environment Setup in Windows 11

```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | more"
```

## Google Cloud Console Setup
1. Visit the [Google Cloud Console](https://cloud.google.com/cloud-console) and create a new project.
2. Search for "Google Drive API" and click **Enable**.
3. In the **Credentials** tab, generate an **OAuth Client ID**.
4. Download the generated JSON file and save it in the `summer-party-four-cuts` folder, renaming it to `credentials.json`.

---

## Deployment and Execution Protocol

### 0. Clone the github
```bash
git clone https://github.com/jihoonkim2100/four_cuts.git
```

### 1. Google API Credential Placement

**Prerequisite:** Ensure the OAuth 2.0 client certificate file issued by the Google Cloud Console is saved as `credentials.json` in the project root directory.

### 2. Run via UV Virtual Environment

```bash
uv run main.py

```

Upon the first network upload, your browser will open to request access to your Google account. After authorization, `token.json` will be cached locally, and subsequent uploads will be handled automatically in the background.

> ### CAUTION: Initial Execution Warning (Token Generation)
> 
> 
> 1. When you run the modified code for the first time and proceed to the upload stage after capturing the photo, your default web browser will open and display the Google login screen.
> 2. Log in with your Google account.
> 3. When prompted with "Do you want to allow the app to access your Google Drive files?", select **Allow**.
> 4. Once you see "The authentication flow has completed" in your browser, you may close the window.
> 5. A `token.json` file will be generated in your local folder; from this point forward, the browser will not open, and authentication/upload will proceed automatically in the background.

By integrating this workflow, files will be instantiated in your cloud environment immediately after the photo is captured, and a QR code with explicit access permissions will be rendered instantly.