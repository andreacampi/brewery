---
name: device-monitor
description: Monitor MiniBrew device status and active brew sessions. Use when checking what's currently brewing, device state, or session progress.
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(date:*)
---

# MiniBrew Device Monitor

Monitor brewing devices and active sessions from the MiniBrew API.

## Quick Status Check

```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/devices/' | jq '.[] | {
    name: .custom_name,
    status: .text,
    active_session: .active_session,
    connection: (if .connection_status == 1 then "online" else "offline" end),
    last_online: .last_time_online
  }'
```

## Get Active Session Details

```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)

# Get device with active session
active_session=$(curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/devices/' | jq -r '.[] | select(.active_session != null) | .active_session')

if [ -n "$active_session" ]; then
  echo "Active session: $active_session"

  # Fetch session details
  curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
    "https://api.minibrew.io/v1/sessions/${active_session}/" | jq '{
      id: .id,
      beer: .beer.name,
      style: .beer.style_name,
      recipe_id: .beer_recipe_id,
      brew_date: (.brew_timestamp | todate),
      status: (if .status == 1 then "active" else "completed" end),
      device_state: .device.process_type
    }'
else
  echo "No active session"
fi
```

## Device States Reference

### `current_state`
- `0` - Idle/Ready
- `1` - Active/Brewing

### `process_type`
- `0` - No process
- `4` - Fermenting (observed in keg device)

### `process_state`
- `0` - Ready/Idle
- `94` - Fermenting (observed during active fermentation)

### `connection_status`
- `0` - Offline
- `1` - Online

### `device_type`
- `0` - Base unit (brewing machine)
- `1` - Keg (fermentation vessel)

## Full Device Status Report

```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)

curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/devices/' | jq -r '.[] | "
Device: \(.custom_name // .serial_number)
Status: \(.text)
Connection: \(if .connection_status == 1 then "online" else "offline" end)
Last online: \(.last_time_online)
Active session: \(.active_session // "none")
Process type: \(.process_type)
Process state: \(.process_state)
---"'
```

## Session Timeline

```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)
session_id="75556"  # Replace with actual session ID

curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  "https://api.minibrew.io/v1/sessions/${session_id}/" | jq '{
    session_id: .id,
    beer_name: .beer.name,
    started: (.brew_timestamp | todate),
    recipe_id: .beer_recipe_id,
    profile_id: .profile,
    original_gravity: .original_gravity,
    og_timestamp: .timestamp_original_gravity
  }'
```

## Find Session by Lot Number

When you know the lot number but need the session ID:

```bash
# Check brew-log.md for the recipe name, then search devices for active sessions
# Manual mapping needed: LOT 099 = session 75556 (Double Hazy Jane)
```

**Note:** There's no direct API link between our lot numbers and MiniBrew session IDs. The mapping must be maintained manually in brew-log.md or by matching beer name + brew date.

## Common Tasks

### Check if any device is currently brewing
```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/devices/' | jq -r '.[] | select(.active_session != null) | "Brewing: \(.beer.name) (session \(.active_session))"'
```

### Get current fermentation progress
```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/devices/' | jq -r '.[] | select(.process_type == 4) | {
    device: .custom_name,
    status: .text,
    since: .last_process_state_change,
    eta: .process_estimate_remaining
  }'
```

### List all devices
```bash
session_token=$(grep session_token auth.yaml | cut -d' ' -f2)
curl -s -H'Client: Breweryportal' -H "Authorization: Bearer $session_token" \
  'https://api.minibrew.io/v1/devices/' | jq -r '.[] | "\(.custom_name // .serial_number) - \(if .connection_status == 1 then "online" else "offline" end)"'
```

## Authentication

If you get auth errors, use the token refresh flow from the community-recipes skill.

## Notes

- Trailing `/` is required on all endpoints
- Session IDs come from `active_session` field in device status
- Recipe IDs in sessions (`beer_recipe_id`) are personal recipes, not community recipes
- The `text` field provides human-readable status (e.g., "is fermenting", "is ready to start a fresh brew")
- Process states may vary - these are observed values, not from official documentation
