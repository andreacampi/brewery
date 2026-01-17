---
name: community-recipes
description: Fetch and sync recipes from MiniBrew online. Use when looking for new recipes, updating the local cache, or checking for recipe updates. For searching existing cached recipes, use recipe-finder instead.
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(mkdir:*), Bash(mv:*), Bash(cp:*), Bash(rm:*), Bash(date:*), Bash(cat:*), Edit, Write
---

# MiniBrew Community Recipes

Fetch and search shared recipes from the MiniBrew API with local caching.

## Cache Location

- `.cache/recipes/` - main cache directory
- `.cache/recipes/recipes.json` - recipe list (metadata)
- `.cache/recipes/{id}.json` - individual recipe files
- `.cache/recipes/.last_fetch` - ISO timestamp of last successful fetch

## Workflow: Check and Update Cache

### Step 1: Check if fetch is needed

```bash
# Check if cache exists
if [ ! -d .cache/recipes ] || [ ! -f .cache/recipes/recipes.json ]; then
  echo "NO_CACHE"  # Need full fetch
elif [ ! -f .cache/recipes/.last_fetch ]; then
  echo "UNKNOWN_AGE"  # Need fetch (can't determine age)
else
  # Check if older than 7 days
  last_fetch=$(cat .cache/recipes/.last_fetch)
  last_ts=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$last_fetch" "+%s" 2>/dev/null || echo 0)
  now_ts=$(date "+%s")
  age_days=$(( (now_ts - last_ts) / 86400 ))
  if [ $age_days -ge 7 ]; then
    echo "STALE"  # Need fetch (older than 7 days)
  else
    echo "FRESH"  # No fetch needed
  fi
fi
```

### Step 2: Fetch into temp directory

Create a temp directory for safe fetching:

```bash
tmp_dir=".cache/recipes.tmp.$(openssl rand -hex 4)"
mkdir -p "$tmp_dir"
```

### Step 3: Fetch recipe list

```bash
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer <session_token>" \
  'https://api.minibrew.io/v1/shared_recipes/?limit=1000' | jq '.' > "$tmp_dir/recipes.json"
```

### Step 4: Compare and fetch individual recipes

For each recipe in the list, check if we need to fetch it:

```bash
# Get list of recipe IDs and their beer.modified timestamps
jq -r '.results[] | "\(.id) \(.beer.modified)"' "$tmp_dir/recipes.json" | while read id api_mod; do
  existing=".cache/recipes/${id}.json"

  if [ -f "$existing" ]; then
    # Compare beer.modified directly (same format in both)
    cached_mod=$(jq -r '.beer.modified' "$existing")
    if [ "$api_mod" = "$cached_mod" ]; then
      echo "SKIP $id (unchanged)"
      continue
    fi
    echo "UPDATE $id (modified)"
  else
    echo "NEW $id"
  fi

  # Fetch the recipe (with rate limiting)
  curl -s -H'Client: Breweryportal' -H "Authorization: Bearer <session_token>" \
    "https://api.minibrew.io/v1/shared_recipes/${id}/" | jq '.' > "$tmp_dir/${id}.json"
  sleep 0.5  # Be nice to the API server
done
```

### Step 5: Merge on success

Only if all fetches succeeded, merge temp into main cache:

```bash
# Ensure main cache directory exists
mkdir -p .cache/recipes

# Copy new/updated files from temp to main cache (preserves existing files)
cp "$tmp_dir"/*.json .cache/recipes/

# Update last fetch timestamp
date -u +"%Y-%m-%dT%H:%M:%S" > .cache/recipes/.last_fetch

# Clean up temp directory
rm -rf "$tmp_dir"
```

### Step 6: Handle errors

If fetch fails partway through:
- Do NOT copy anything to main cache
- Clean up temp directory
- Report which recipes failed
- Main cache remains intact

```bash
# On error
rm -rf "$tmp_dir"
echo "Fetch failed. Cache unchanged."
```

## API Reference

**Base URL:** `https://api.minibrew.io/`

**Required Headers:**
- `Client: Breweryportal` (exact value required)
- `Authorization: Bearer <session_token>` (for queries)

**Notes:**
- Trailing `/` on endpoints is important
- Version (v1/, v2/) is part of the endpoint path

## Credentials

Stored in `auth.yaml` (not committed):
- `email` - account email
- `auth_token` - long-lived auth token (for TOKEN header)
- `session_token` - short-lived request token (for Bearer header)
- `user_id` - user ID for filtering results

## Authentication Flow

**When you get an auth error:**
1. First, try to refresh the session token
2. If refresh fails, ask the user for their password and get a new token
3. Never store the password - use it only for the single API call, then forget it

### Refresh Token

```bash
curl -s -X POST -H'Client: Breweryportal' \
  -H "Authorization: TOKEN <auth_token>" \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<session_token>"}' \
  https://api.minibrew.io/v2/token/refresh/
```
Response: `{"token":"<new_token>","exp":<unix_timestamp>}` → update `session_token` in `auth.yaml`

### Get New Token (if refresh fails)

Ask the user for their password, then:
```bash
curl -s -X POST -H'Client: Breweryportal' \
  -H "Authorization: TOKEN <auth_token>" \
  -H 'Content-Type: application/json' \
  -d '{"email":"<email>","password":"<password>"}' \
  https://api.minibrew.io/v2/token/
```
Response: `{"token":"<new_token>","exp":<unix_timestamp>}` → update `session_token` in `auth.yaml`

## Utility Scripts

### Cache Status

```bash
echo "Recipes: $(ls .cache/recipes/*.json 2>/dev/null | wc -l | tr -d ' ')"
echo "Last fetch: $(cat .cache/recipes/.last_fetch 2>/dev/null || echo 'never')"
```

### Preview Changes (dry run)

Count NEW/UPDATE/SKIP without fetching:

```bash
# First fetch the recipe list to a temp location
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer <session_token>" \
  'https://api.minibrew.io/v1/shared_recipes/?limit=1000' > /tmp/recipes_check.json

# Count each category
jq -r '.results[] | "\(.id) \(.beer.modified)"' /tmp/recipes_check.json | while read id api_mod; do
  cached_file=".cache/recipes/${id}.json"
  if [ -f "$cached_file" ]; then
    cached_mod=$(jq -r '.beer.modified' "$cached_file")
    if [ "$api_mod" = "$cached_mod" ]; then
      echo "SKIP"
    else
      echo "UPDATE"
    fi
  else
    echo "NEW"
  fi
done | sort | uniq -c
```

### List Updated Recipes

Show which recipes have been modified:

```bash
jq -r '.results[] | "\(.id) \(.beer.modified) \(.beer.name)"' .cache/recipes/recipes.json | while read id api_mod name; do
  cached_file=".cache/recipes/${id}.json"
  if [ -f "$cached_file" ]; then
    cached_mod=$(jq -r '.beer.modified' "$cached_file")
    if [ "$api_mod" != "$cached_mod" ]; then
      echo "$id | $name | $api_mod"
    fi
  fi
done | column -t -s'|'
```

### Full Fetch with Progress

Complete fetch script with progress reporting:

```bash
# Setup
tmp_dir=".cache/recipes.tmp.$(openssl rand -hex 4)"
mkdir -p "$tmp_dir"

# Get credentials
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)

# Fetch recipe list
echo "Fetching recipe list..."
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/shared_recipes/?limit=1000' | jq '.' > "$tmp_dir/recipes.json"

# Find recipes to fetch
echo "Comparing with cache..."
jq -r '.results[] | "\(.id) \(.beer.modified)"' "$tmp_dir/recipes.json" | while read id api_mod; do
  cached_file=".cache/recipes/${id}.json"
  if [ -f "$cached_file" ]; then
    cached_mod=$(jq -r '.beer.modified' "$cached_file")
    [ "$api_mod" != "$cached_mod" ] && echo "$id"
  else
    echo "$id"
  fi
done > "$tmp_dir/to_fetch.txt"

total=$(wc -l < "$tmp_dir/to_fetch.txt" | tr -d ' ')
echo "Recipes to fetch: $total"

# Fetch with progress
count=0
while read id; do
  count=$((count + 1))
  [ $((count % 20)) -eq 0 ] && echo "Progress: $count/$total"
  curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
    "https://api.minibrew.io/v1/shared_recipes/${id}/" | jq '.' > "$tmp_dir/${id}.json"
  sleep 0.5
done < "$tmp_dir/to_fetch.txt"

# Merge
echo "Merging..."
cp "$tmp_dir"/*.json .cache/recipes/
date -u +"%Y-%m-%dT%H:%M:%S" > .cache/recipes/.last_fetch
rm -rf "$tmp_dir"

echo "Done. Cache now has $(ls .cache/recipes/*.json | wc -l | tr -d ' ') recipes"
```

## Notes

- Old recipes are never deleted from cache (assumption - verify later)
- Merge strategy: new files added, existing updated only if `beer.modified` differs
- Safe update: temp directory prevents partial updates on failure
- Compare `beer.modified` directly (same ISO format in API list and cached files)
