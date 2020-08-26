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

_Example: I am currently using this integration to subscribe to the `User's presence status has been updated` event which occurs every time I enter or exit a meeting. A webhook automation gets triggered on each status change and enables/disables a `do not disturb` signal for my wife._

Because the event name is included in the JSON payload sent to the webhook, you can subscribe to any events you would like within the same app and use automation `conditions` to conditionally do different things depending on the event. **If you are just interested in setting up this integration to monitor when someone is on or off a Zoom call, skip the Installation section to the "Easy Installation - Binary Sensor that indicates when the user is on a call" section**

## Pre-Requisites

Your Home Assistant instance must be externally accessible from the Internet.

## Installation

### Easy Installation - Automatic Binary Sensor that indicates when the user is on a call

This installation method only supports monitoring the `User's presence status has been updated` event meaning you will get an out of the box binary sensor to track your Zoom presence but you will not be monitor any other events.

<details><summary>Expand</summary>

#### Set up your Zoom app

1. Go to the [Build App](https://marketplace.zoom.us/develop/create) page.
2. Click on `Create` in the OAuth card.
3. Enter an application name of your choice, select `User-managed app`, deselect `Would you like to publish this app on Zoom App Marketplace?`, and then click on `Create`.
4. Copy your `Client ID` and `Client Secret` somewhere as you will need them later to configure Home Assistant.
5. Enter the following `Redirect URL for OAuth`: `<BASE_HA_URL>/auth/external/callback` (replace `<BASE_HA_URL>` with the URL you use to access Home Assistant, e.g. `https://ha.example.com`)
6. Enter your `<BASE_HA_URL>` in the `Whitelist URL` section, then hit `Continue`.
7. The `App Name` should already be filled out. A `Short Description` and `Long Description` are required, but since this app is only for you, it doesn't matter what you enter here. Click `Continue` once you are done.
8. Enable `Event Subscriptions` and click on `Add new event subscriptions`.
9. Enter a name for this subscription (does not matter).
10. Your `Event notification endpoint URL` should be set to `<BASE_HA_URL>/api/webhook/<WEBHOOK_ID>`. Use any ID that you already aren't using in your Home Assistant instance. I generated mine using a [GUID Generator](https://www.guidgenerator.com/). Remember this ID for later.
11. Now click on `Add events`. From this menu, go to the `User Activity` event type and check the box next to `User's presence status has been updated`.
12. Cick `Done`, then `Save` the subscription before hitting `Continue`.
13. The `Scopes` section should have `View your user information /user:read` listed there and that's it. Click `Continue`.
14. You are now ready to configure Home Assistant!

#### Configure HomeAssistant

You can either do the initial setup through the UI or in your `configuration.yaml` file. Both methods are described below.

#### Using the UI

1. Click Install
2. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom Automation". Select it.
3. You will be asked to provide the `Client ID` and `Client Secret` that Zoom gave you earlier as well as the `Webhook ID` as you configured it in the earlier section. Enter them in and click `Submit`.
4. Skip to "Finish Setup" section below

#### Using configuration.yaml

1. Click Install
2. Create a new top level configuration item in `configuration.yaml` as follows (you may need to restart your HA instance to pick up the changes once they are added):
```yaml
zoom_automation:
    client_id: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
    client_secret: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
    webhook_id: <WEBHOOK_ID_FROM_THE_EVENT_SUBSCRIPTIONS_PAGE_OF_SETTING_UP_YOUR_CUSTOM_ZOOM_APP>
```
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom Automation". Select it.
4. Skip to "Finish Setup" section below

#### Finish setup

5. Enter a name for the account you plan to connect to Zoom. This will be useful if you plan to monitor more than one Zoom account.
6. If you are not already logged into Zoom, you will be asked to log in.
7. Authorize the app for the `Scopes` that were configured earlier.
8. Once it is complete, you will now have a new binary sensor called `binary_sensor.zoom_<ACCOUNT_NAME_YOU_CONFIGURED_IN_STEP_5>`. When it is `On`, that user is on a Zoom call, and when it is `Off`, they are not.

> NOTE: Once you have configured the `client_id`, `client_secret`, and `webhook_id`, you can monitor as many Zoom accounts as you want. Just make sure you are logged out of Zoom, then add the `Zoom Automation` integration again from the Integrations menu, and login to the next account when asked. For each account you log in to, a new binary sensor will be created for that account.

</details>

### Advanced Installation - You set up your own webhook automations but you can monitor any Zoom event

This installation method does very little out of the box but allows you to build your own automations to consume any Zoom event (check out [Webhook Reference docs](https://marketplace.zoom.us/docs/api-reference/webhook-reference) to see what types of events you can consume). Typically these automations would set the state of an `input_text` entity, and then you can build automations using the state of those entities to do something else e.g. turn on a red light or send a Slack message.

<details><summary>Expand</summary>

#### Set up your Zoom app

1. Go to the [Build App](https://marketplace.zoom.us/develop/create) page.
2. Click on `Create` in the OAuth card.
3. Enter an application name of your choice, select `User-managed app`, deselect `Would you like to publish this app on Zoom App Marketplace?`, and then click on `Create`.
4. Copy your `Client ID` and `Client Secret` somewhere as you will need them later to configure Home Assistant.
5. Enter the following `Redirect URL for OAuth`: `<BASE_HA_URL>/auth/external/callback` (replace `<BASE_HA_URL>` with the URL you use to access Home Assistant, e.g. `https://ha.example.com`)
6. Enter your `<BASE_HA_URL>` in the `Whitelist URL` section, then hit `Continue`.
7. The `App Name` should already be filled out. A `Short Description` and `Long Description` are required, but since this app is only for you, it doesn't matter what you enter here. Click `Continue` once you are done.
8. Enable `Event Subscriptions` and click on `Add new event subscriptions`.
9. Enter a name for this subscription (does not matter).
10. Your `Event notification endpoint URL` should be set to `<BASE_HA_URL>/api/webhook/<WEBHOOK_ID>`. Use any ID that you already aren't using in your Home Assistant instance. I generated mine using a [GUID Generator](https://www.guidgenerator.com/). Remember this ID for later.
11. Now click on `Add events`. From this menu, you can choose what events you want to subscribe to. For my example from earlier, you would go to the `User Activity` event type and check the box next to `User's presence status has been updated`. If you want to get more details about when you start a meeting, add `Start Meeting` under `Meeting`.
12. Once you are done, click `Done`, then `Save` the subscription before hitting `Continue`.
13. The `Scopes` section should already be updated to the permissions the app would need for the events you selected earlier. Click `Continue`.
14. You are now ready to configure Home Assistant!

#### Configure HomeAssistant

You can either do the initial setup through the UI or in your `configuration.yaml` file. Both methods are described below.

#### Using the UI

1. Click Install
2. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom Automation". Select it.
3. You will be asked to provide the `Client ID` and `Client Secret` that Zoom gave you earlier (do not enter a `Webhook ID`, that is used for the easy install below and will not allow you to build custom webhook automations). Enter them in and click `Submit`.
4. Skip to "Finish Setup" section below

#### Using configuration.yaml

1. Click Install
2. Create a new top level configuration item in `configuration.yaml` as follows (you may need to restart your HA instance to pick up the changes once they are added):
```yaml
zoom_automation:
    client_id: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
    client_secret: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
```
> NOTE: Do not include a `webhook_id`, that is used for the easy install below and will not allow you to build custom webhook automations
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom Automation". Select it.
4. Skip to "Finish Setup" section below

#### Finish setup

5. Enter a name for the account you plan to connect to Zoom. This will be useful if you plan to monitor more than one Zoom account.
6. If you are not already logged into Zoom, you will be asked to log in.
7. Authorize the app for the `Scopes` that were configured earlier.
8. Start automating!

> NOTE: Once your app is configured and activated, you can go back to Zoom at any time to update the events you are subscribed to. To do this, go to your [Created Apps list](https://marketplace.zoom.us/user/build) and click on the app name. Go to the `Feature` section and expand `Event Subscriptions`. You can either edit your existing subscription and update it, which will send all of the different events through the same webhook, or create a new subscription and route it to a different webhook, your choice! Once you are done, you should check the `Scopes` section to make sure the permissions make sense for the events you selected. In my testing Zoom does a good job of updating this based on the scopes you select. Once you are done with that, you should remove the integration from the Integrations menu in the HA UI and re-add it. You may need to reauthorize the application if the scopes required have changed.

</details>

## Monitoring more than one Zoom account

In some cases, you may want to receive events for more than one Zoom account.

You can add the Zoom integration as many times as you would like with a single `client_id`/`client_secret` configured by going back to the Integrations UI and adding `Zoom Automation` again. As long as you log off Zoom after each time, you will be able to connect your app to each account you want to monitor.

Events from all of the linked accounts will all be sent to the same `webhook_id`, so in order to create sensible automations, you will need to be able to distinguish between accounts. The integration will add a new sensor for each account that gets linked called `sensor.zoom_{LOWERCASE_NAME_WITH_UNDERSCORES_INSTEAD_OF_SPACES}_user_profile` which contains profile information about the account. You can use the `id`, `email`, or `account_id` attributes of the sensor to identify events coming from the account. The information you need from the webhook event to match to the correct account will be in different places depending on the event type. In addition, you should lowercase both the property from the event and the sensor data to ensure a match. In testing I found that Zoom sends a lowercase `id`, so it just seems like the safer approach.

### Example
For the `user.presence_status_updated` event, a `user_id` is provided by `trigger.json.payload.object.id`. I can match that to the id of the entry for `Hello Worlds` as follows :
```yaml
condition:
  condition: template
  value_template: '{{ trigger.json.payload.object.id.lower() == state_attr('sensor.zoom_hello_world_user_profile', 'id').lower() }}'
```

## Creating Automations

You are free to create automations however you see fit, but here are some tips:

### Trigger

Your trigger configuration should be as follows:
```yaml
trigger:
    platform: webhook
    webhook_id: <THE_WEBHOOK_ID_YOU_SET_UP_IN_YOUR_CUSTOM_ZOOM_APP>
```

### Conditions and Actions

To see the schema of various events, check Zoom's [Webhook Reference docs](https://marketplace.zoom.us/docs/api-reference/webhook-reference). On the left hand side navigation, you can click into the various Event types and see the format of the JSON that will be sent to your webhook.

To create a condition on an event type, use something like the following:
```yaml
condition:
  condition: template
  value_template: '{{ trigger.json.event == "user.presence_status_updated" }}'
```

You will likely want to act on information in `trigger.json.payload.object`, either in a `condition` or an `action`. Be sure to use `value_template` and `data_template` when accessing this information in your configured automation.

You can use some `input_text`s with an automation too, like this:

<details><summary>Expand</summary>

```yaml
- alias: Zoom status updates
  description: ''
  trigger:
  - platform: webhook
    webhook_id: b44915ce-7a7a-43c8-953a-23c35d790097
  condition: []
  action:
  - choose:
    - conditions:
      - condition: template
        value_template: '{{ trigger.json.event == "user.presence_status_updated" }}'
      sequence:
      - data_template:
          entity_id: input_text.zoom_status
          value: '{{ trigger.json.payload.object.presence_status }}'
        service: input_text.set_value
    - conditions:
      - condition: template
        value_template: '{{ trigger.json.event == "meeting.started" }}'
      sequence:
      - data_template:
          entity_id: input_text.zoom_meeting
          value: '{{ trigger.json.payload.object.topic }}'
        service: input_text.set_value
  mode: single
```

</details>

<!---->

***

[zoom]: https://zoom.us/
[commits-shield]: https://img.shields.io/github/commit-activity/y/raman325/ha-zoom-automation.svg?style=for-the-badge
[commits]: https://github.com/raman325/ha-zoom-automation/commits/master
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/raman325/ha-zoom-automation.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40raman325-blue?style=for-the-badge
[last-commit-shield]: https://img.shields.io/github/last-commit/raman325/ha-zoom-automation?style=for-the-badge
