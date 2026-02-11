# Testing the ADO Migration Readiness Analyzer UI

## Prerequisites
- Backend running on http://localhost:8000
- Frontend running on http://localhost:5173
- Azure DevOps PAT with read permissions
- GitHub PAT with repo creation permissions (for migration)
- `gh gei` extension installed (for migration)

---

## Step-by-Step Testing Guide

### Step 1: Open the Dashboard
1. Go to **http://localhost:5173**
2. You should see a welcome screen saying "Configure your Azure DevOps connection"
3. ✅ **Pass**: Welcome message appears with "Configure Connection" button

---

### Step 2: Configure Azure DevOps Connection
1. Click **Configure** in the navigation (or the button)
2. Fill in:
   - **Organization URL**: `https://dev.azure.com/YOUR-ORG` (e.g., `https://dev.azure.com/octodemo-msft`)
   - **PAT**: Your Azure DevOps Personal Access Token
3. Click **Save & Continue**
4. ✅ **Pass**: Green success message "Connected successfully! Found X projects"
5. ❌ **Fail**: Red error message - check your PAT and URL

---

### Step 3: Scan Your Organization
1. You'll be redirected to the **Scan** page (or click Scan in nav)
2. Optionally select a specific project, or leave as "All Projects"
3. Click **Start Scan**
4. Watch the progress bar fill up
5. ✅ **Pass**: Progress bar completes, redirects to Dashboard
6. ❌ **Fail**: Error message appears

---

### Step 4: View Dashboard Results
1. After scan, the Dashboard shows:
   - **Stat cards**: Repositories, Pipelines, Work Items, Projects counts
   - **Complexity meter**: Score out of 100 with Low/Medium/High rating
   - **Blockers**: List of migration blockers (if any)
2. ✅ **Pass**: All cards show real numbers from your ADO org

---

### Step 5: View Detailed Report
1. Click **Report** in the navigation
2. You should see:
   - Complexity bar charts
   - Asset distribution pie chart
   - Expandable project list (click to expand)
3. Click **Export JSON** to download the report
4. ✅ **Pass**: Charts render, projects expand, JSON downloads

---

### Step 6: Test Migration (Requires GEI Setup)

#### Prerequisites for Migration:
```cmd
# Install GitHub CLI GEI extension
gh extension install github/gh-gei

# Authenticate
gh auth login
```

#### Configure GitHub Target:
1. Go to **Configure** page
2. Fill in the **GitHub** section:
   - **Target Organization**: Your GitHub org name (e.g., `nkusakula`)
   - **Personal Access Token**: Your GitHub PAT (needs `repo` scope)
3. Save the configuration

#### Perform Migration:
1. Click **Migrate** in the navigation
2. You should see a list of repositories from your ADO org
3. Use the **search box** to filter repos
4. **Click checkboxes** to select repos to migrate
5. Verify:
   - **Target GitHub Organization** is correct
   - **Visibility** is set (private/internal/public)
6. Click **Start Migration**
7. Watch the progress panel on the right
8. ✅ **Pass**: Repos show checkmarks (✓) when completed
9. ❌ **Fail**: Repos show X marks with error

---

## Quick Test Checklist

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open http://localhost:5173 | Dashboard loads |
| 2 | Configure → Enter ADO URL + PAT → Save | "Connected successfully" |
| 3 | Scan → Start Scan | Progress bar fills, redirects |
| 4 | Dashboard | Shows repo/pipeline/work item counts |
| 5 | Report | Charts render, projects expandable |
| 6 | Migrate → Select repos → Start | Repos migrate with progress |

---

## Troubleshooting

### "Not configured" error
- Go to Configure page and enter your credentials

### "Connection failed" error
- Check your ADO organization URL format
- Verify your PAT hasn't expired
- Ensure PAT has required scopes (Code, Build, Work Items - Read)

### Scan stuck at 0%
- Check backend terminal for errors
- Refresh the page and try again

### Migration fails
- Ensure `gh gei` extension is installed
- Run `gh auth status` to verify GitHub auth
- Check you have permission to create repos in target org

### Charts not showing
- Try a hard refresh (Ctrl+Shift+R)
- Check browser console for errors (F12)

---

## API Health Check

You can also test the backend directly:

```bash
# Health check
curl http://localhost:8000/api/health

# Get config status
curl http://localhost:8000/api/config

# Test connection (after configuring)
curl http://localhost:8000/api/test-connection

# Get scan results (after scanning)
curl http://localhost:8000/api/scan/results
```
