# This project is no longer actively maintained

I switched jobs in 2021 and no longer use Zoom so I am unable to continue developing this integration further. I would be happy to transfer ownership or add contributers, and in lieu of that I will review PRs and accept contributions. Please open an issue if you would like to take a more active role in this integration.


[![Last Commit][last-commit-shield]][commits]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]](hacs.json)
[![Project Maintenance][maintenance-shield]](https://github.com/raman325)

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Component to help create automations for events that occur in your [Zoom][zoom] account._

{% if installed %}

## Uninstall

If you choose to uninstall this integration, be sure to go to [the installed apps list](https://marketplace.zoom.us/user/installed) in your Zoom account and uninstall the app from there, otherwise it will continue to send events to your HA instance.

{% endif %}

## Background

Zoom allows users to create custom applications that can trigger a JSON POST to a webhook when certain events in your Zoom account occur. This component will enable you to activate a custom Zoom app for your account which you can then use to subscribe to Zoom events.

_Example: I am currently using this integration to subscribe to the `User's presence status has been updated` event which occurs every time I enter or exit a meeting. An event automation gets triggered on each status change and enables/disables a `do not disturb` signal for my wife._

Because the event name is included in the JSON payload sent to the webhook, you can subscribe to any events you would like within the same app and use automation `conditions` to conditionally do different things depending on the event.

## Pre-Requisites

Your Home Assistant instance must be externally accessible from the Internet. The `External URL` will also need to be appropriately set and should replace `<BASE_HA_URL>` references in the installation instructions. You can do this in your `configuration.yaml` or through the UI as mention [in the docs](https://www.home-assistant.io/docs/configuration/basic/).

## Installation (Single AccounzRMonitoring)

> NOTE: If you want to monitor multiple Zoom accounts, skip to the next set of installation instructions

<details><summary>Sensors Provided</summary>

You will get a binary sensor out of the box:

|  | Description |
|-|-|
| Name | `binary_sensor.zoom_{PROVIDED_ACCOUNT_NAME}` |
| Purpose | Tracks user presence on a Zoom call by consuming the  `User's presence status has been updated`  event. If the state is `on`, the user is on a Zoom call. |
| Notes | If  `User's presence status has been updated`  is not enabled in the Zoom App's Event Subscriptions, this sensor will not work and can be disabled. |

</details>

<details><summary>Installation Instructions</summary>

### Set up your Zoom app

1. Go to the [Build App](https://marketplace.zoom.us/develop/create) page.
2. Click on `Create` in the OAuth card.
3. Enter an application name of your choice, select `User-managed app`, deselect `Would you like to publish this app on Zoom App Marketplace?`, and then click on `Create`.
4. Copy your `Client ID` and `Client Secret` somewhere as you will need them later to configure Home Assistant.
5. Enter the following `Redirect URL for OAuth`: `<BASE_HA_URL>/auth/external/callback` (replace `<BASE_HA_URL>` with the URL you configured inside of Home Assistant as the external URL, e.g. `https://ha.example.com`)
6. Enter your `<BASE_HA_URL>` in the `Add Allow List` section, then hit `Continue`.
7. The `App Name` should already be filled out. A `Short Description` and `Long Description` are required, but since this app is only for you, it doesn't matter what you enter here. You will also need to add a `Name` and `Email Address` in the `Developer Contact Information` section. Click `Continue` once you are done.
8. Enable `Event Subscriptions` and click on `Add new event subscriptions`.
9. Enter a name for this subscription (does not matter).
10. Your `Event notification endpoint URL` should be set to `<BASE_HA_URL>/api/zoom`.
11. Now click on `Add events`. From this menu, you can choose what events you want to subscribe to. To use the `binary_sensor` provided by the integration, you would go to the `User Activity` event type and check the box next to `User's presence status has been updated`. If you want to get more details about when you start a meeting, add `Start Meeting` under `Meeting`.
12. Make note of the `Secret Token` found under `Features` > `Access` as you will need it for your configuration later.
13. Once you are done, click `Done`, then `Save` the subscription before hitting `Continue`.
14. The `Scopes` section should have already be updated to include at least one permission based on the events you choose to monitor. If you want to use the `binary_sensor`, you will need to add another scope so that the initial status of your sensor is set correctly, otherwise the integration will naively restore your last state on restart. To do this, click `Add Scopes` in the top right of the main page, go to the `Team Chat` section, enable the checkbox next to `View current user's team chat contact information` (the scope is called `chat_contact:read`) and click `Done`. Click `Continue` to save what you did.
15. You are now ready to configure Home Assistant!

### Install the Zoom integration via HACS

If you don't already have HACS installed, follow the [instructions here](https://hacs.xyz/docs/installation/manual). Once HACS has been installed, go the HACS menu in your sidebar menu, go to Integrations, and click Add. Search for Zoom and select `INSTALL THIS REPOSITORY IN HACS`. You may need to restart your Home Assistant instance in order for it to be able to see the new integration. You may also need to hard refresh the UI in order to see the Integration in the main Integrations menu.

### Configure HomeAssistant

You can either do the initial setup through the UI or in your `configuration.yaml` file. Both methods are described below.

#### Using the UI

1. Click Install
2. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom". Select it.
3. You will be asked to provide the `Client ID` and `Client Secret` that Zoom gave you earlier as well as the `Secret Token` you grabbed from Zoom in the earlier section. Enter them in and click Submit.
4. Skip to "Finish Setup" section below

#### Using configuration.yaml

1. Click Install
2. Create a new top level configuration item in `configuration.yaml` as follows (you may need to restart your HA instance to pick up the changes once they are added):
```yaml
zoom:
    client_id: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
    client_secret: <CLIENT_SECRET_FROM_YOUR_CUSTOM_ZOOM_APP>
    secret_token: <SECRET_TOKEN_FROM_FEATURES_ACCESS_IN_YOUR_CUSTOM_ZOOM_APP>
```
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom". Select it.
4. Skip to "Finish Setup" section below

### Finish setup

5. Enter a name for the account you plan to connect to Zoom. This will be useful if you plan to monitor more than one Zoom account.
6. If you are not already logged into Zoom, you will be asked to log in.
7. Authorize the app for the `Scopes` that were configured earlier.
8. Start automating!

> NOTE: Once your app is configured and activated, you can go back to Zoom at any time to update the events you are subscribed to. To do this, go to your [Created Apps list](https://marketplace.zoom.us/user/build) and click on the app name. Go to the `Feature` section and expand `Event Subscriptions`, then edit your existing subscription and update it. Once you are done, you should check the `Scopes` section to make sure the permissions make sense for the events you selected. In my testing Zoom does a good job of updating this based on the scopes you select. Once you are done with that, you should remove the integration from the Integrations menu in the HA UI and re-add it. You may need to reauthorize the application if the scopes required have changed.

</details>

## Installation (Multiple Account Monitoring)

<details><summary>Sensors Provided</summary>

You will get a binary sensor out of the box:

|  | Description |
|-|-|
| Name | `binary_sensor.zoom_{PROVIDED_ACCOUNT_NAME}` |
| Purpose | Tracks user presence on a Zoom call by consuming the  `User's presence status has been updated`  event. If the state is `on`, the user is on a Zoom call. |
| Notes | If  `User's presence status has been updated`  is not enabled in the Zoom App's Event Subscriptions, this sensor will not work and can be disabled. |

</details>

<details><summary>Installation Instructions</summary>

### Set up your Zoom app (do this for each account you want to monitor)

1. Go to the [Build App](https://marketplace.zoom.us/develop/create) page.
2. Click on `Create` in the OAuth card.
3. Enter an application name of your choice, select `User-managed app`, deselect `Would you like to publish this app on Zoom App Marketplace?`, and then click on `Create`.
4. Copy your `Client ID` and `Client Secret` somewhere as you will need them later to configure Home Assistant.
5. Enter the following `Redirect URL for OAuth`: `<BASE_HA_URL>/auth/external/callback` (replace `<BASE_HA_URL>` with the URL you configured inside of Home Assistant as the external URL, e.g. `https://ha.example.com`)
6. Enter your `<BASE_HA_URL>` in the `Whitelist URL` section, then hit `Continue`.
7. The `App Name` should already be filled out. A `Short Description` and `Long Description` are required, but since this app is only for you, it doesn't matter what you enter here. You will also need to add a `Name` and `Email Address` in the `Developer Contact Information` section. Click `Continue` once you are done.
8. Make note of the `Secret Token` found under `Features` > `Access` as you will need it for your configuration later.
9. Enable `Event Subscriptions` and click on `Add new event subscriptions`.
10. Enter a name for this subscription (does not matter).
11. Your `Event notification endpoint URL` should be set to `<BASE_HA_URL>/api/zoom`.
12. Now click on `Add events`. From this menu, you can choose what events you want to subscribe to. To use the `binary_sensor` provided by the integration, you would go to the `User Activity` event type and check the box next to `User's presence status has been updated`. If you want to get more details about when you start a meeting, add `Start Meeting` under `Meeting`.
13. Once you are done, click `Done`, then `Save` the subscription before hitting `Continue`.
14. The `Scopes` section should have already be updated to include at least one permission based on the events you choose to monitor. If you want to use the `binary_sensor`, you will need to add another scope so that the initial status of your sensor is set correctly, otherwise the integration will naively restore your last state on restart. To do this, click `Add Scopes` in the top right of the main page, go to the `Chat` section, enable the checkbox next to `View current user's chat contact information` (the scope is called `chat_contact:read`) and click `Done`. Click `Continue` to save what you did.
15. You are now ready to configure Home Assistant!

### Install the Zoom integration via HACS

If you don't already have HACS installed, follow the [instructions here](https://hacs.xyz/docs/installation/manual). Once HACS has been installed, go the HACS menu in your sidebar menu, go to Integrations, and click Add. Search for Zoom and select `INSTALL THIS REPOSITORY IN HACS`. You may need to restart your Home Assistant instance in order for it to be able to see the new integration. You may also need to hard refresh the UI in order to see the Integration in the main Integrations menu.

### Configure HomeAssistant

You can either do the initial setup through the UI or in your `configuration.yaml` file. Both methods are described below.

1. Click Install
2. Create a new top level configuration item in `configuration.yaml` as follows (you will need to restart your HA instance to pick up the changes once they are added):
```yaml
zoom:
  - client_id: <ACCOUNT1_CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
    client_secret: <ACCOUNT1_CLIENT_SECRET_FROM_YOUR_CUSTOM_ZOOM_APP>
    secret_token: <ACCOUNT1_SECRET_TOKEN_FROM_FEATURES_ACCESS>
    name: ACCOUNT1 (make sure you use a name that will make it easy for you to know which Zoom account to log into later)
  - client_id: <ACCOUNT2_CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
    client_secret: <ACCOUNT2_CLIENT_SECRET_FROM_YOUR_CUSTOM_ZOOM_APP>
    secret_token: <ACCOUNT2_SECRET_TOKEN_FROM_FEATURES_ACCESS>
    name: ACCOUNT2 (make sure you use a name that will make it easy for you to know which Zoom account to log into later)
```
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom". Select it.
4. Select the name for the account you want to link to.
6. If you are not already logged into Zoom, you will be asked to log in. You must log into the account that the Zoom app that uses the credentials from step 4 is created in.
7. Authorize the app for the `Scopes` that were configured earlier.
8. Start automating!

> NOTE: Once your app is configured and activated, you can go back to Zoom at any time to update the events you are subscribed to. To do this, go to your [Created Apps list](https://marketplace.zoom.us/user/build) and click on the app name. Go to the `Feature` section and expand `Event Subscriptions`, then edit your existing subscription and update it. Once you are done, you should check the `Scopes` section to make sure the permissions make sense for the events you selected. In my testing Zoom does a good job of updating this based on the scopes you select. Once you are done with that, you should remove the integration from the Integrations menu in the HA UI and re-add it. You may need to reauthorize the application if the scopes required have changed.

</details>

## Change Zoom status to binary sensor state mapping

By default, the binary sensor will be `on`, or `Connected`, when your Zoom account is in the following statuses:
- `In_Meeting`
- `Presenting`
- `On_Phone_Call`

All other statuses will cause the binary sensor to be `off`, or `Disconnected`. If you'd like to change this behavior, you can update which statuses are used to determine when the binary sensor is `on` by using the Options config flow as follows:

1. Navigate to "Configuration" -> "Integrations" and look for the Zoom card
2. Click the "Options" link on the card
3. Select your statuses
4. Click "Submit" to apply the changes

## Monitoring custom events (non-presence related)

Events from all of the linked accounts will all be sent using the same event, so in order to create sensible automations, you will need to be able to distinguish between accounts. The `binary_sensor` created for each account you link to will have all of the profile information you need. You can use the `id`, `email`, or `account_id` attributes of the sensor to identify events coming from the account. The information you need from the webhook event to match to the correct account will be in different places depending on the event type. In addition, you should lowercase both the property from the event and the sensor data to ensure a match. In testing I found that Zoom sends a lowercase `id`, so it just seems like the safer approach.

### Example

For the `user.presence_status_updated` event, a `user_id` is provided by `trigger.event.data.payload.object.id`. I can match that to the id of the entry for `Hello Worlds` as follows :
```yaml
condition:
  - {{ trigger.event.data.payload.object.id.lower() == state_attr('binary_sensor.zoom_hello_world', 'id').lower() }}
```

## Creating Automations

You are free to create automations however you see fit, but here are some tips:

### Trigger

Your trigger configuration should be as follows:
```yaml
trigger:
  platform: event
  event_type: zoom_webhook
  event_data:
    event: <ZOOM_EVENT_NAME>
```

### Conditions and Actions

To see the schema of various events, check Zoom's [Webhook Reference docs](https://marketplace.zoom.us/docs/api-reference/webhook-reference). On the left hand side navigation, you can click into the various Event types and see the format of the JSON that will be sent to HA.

To create a condition on an event type, use something like the following:
```yaml
condition:
  condition: "{{ trigger.event.data.event == "user.presence_status_updated" }}"
```

You will likely want to act on information in `trigger.event.data.payload.object`, either in a `condition` or an `action`. Be sure to use `value_template` and `data_template` when accessing this information in your configured automation if HA version is below 0.115.0.

You can use some `input_text`s with an automation too, like this:

<details><summary>Expand</summary>

```yaml
- alias: Zoom status updates
  description: ''
  trigger:
  - platform: event
    event_type: zoom_webhook
  condition: []
  action:
  - choose:
    - conditions: "{{ trigger.event.data.event == "user.presence_status_updated" }}"
      sequence:
      - data:
          entity_id: input_text.zoom_status
          value: '{{ trigger.event.data.payload.object.presence_status }}'
        service: input_text.set_value
    - conditions: "{{ trigger.event.data.event == "meeting.started" }}"
      sequence:
      - data:
          entity_id: input_text.zoom_meeting
          value: '{{ trigger.event.data.payload.object.topic }}'
        service: input_text.set_value
  mode: single
```

</details>

<!---->

***

[zoom]: https://zoom.us/
[commits-shield]: https://img.shields.io/github/commit-activity/y/raman325/ha-zoom-automation.svg?style=for-the-badge
[commits]: https://github.com/raman325/ha-zoom-automation/commits/master
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/raman325/ha-zoom-automation.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40raman325-blue?style=for-the-badge
[last-commit-shield]: https://img.shields.io/github/last-commit/raman325/ha-zoom-automation?style=for-the-badge
