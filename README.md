[![Last Commit][last-commit-shield]][commits]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]](hacs)
![Project Maintenance][maintenance-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Component to help create automations for events that occur in your [Zoom][zoom] account._

Zoom allows users to create custom applications that can trigger a JSON POST to a webhook when certain events in your Zoom account occur. This component will enable you to activate a custom Zoom app for your account which you can then use to subscribe to Zoom events. As an example, I am currently using this integration to subscribe to the `User's presence status has been updated` event which gets triggered any time I enter or exit a meeting and creates a `do not disturb` signal for my wife. Because the event name is included in the JSON payload sent to the webhook, you can subscribe to any events you would like within the same app and use automation `conditions` to conditionally do different things depending on the event.

{% if not installed %}

## Pre-Requisites

Your Home Assistant instance must be externally accessible from the Internet.

## Installation

### Set up your Zoom app

1. Go to the ![Build App][https://marketplace.zoom.us/develop/create] page.
2. Click on `Create` in the OAuth card.
3. Enter an application name of your choice, select `User-managed app`, deselect `Would you like to publish this app on Zoom App Marketplace?`, and then click on `Create`.
4. Copy your `Client ID` and `Client Secret` somewhere as you will need them later to configure Home Assistant.
5. Enter the following `Redirect URL for OAuth`: `<BASE_HA_URL>/auth/external/callback` (replace `<BASE_HA_URL>` with the URL you use to access Home Assistant, e.g. `https://ha.example.com`)
6. Enter your `<BASE_HA_URL>` in the `Whitelist URL` section, then hit `Continue`.
7. The `App Name` should already be filled out. A `Short Description` and `Long Description` are required, but since this app is only for you, it doesn't matter what you enter here. Click `Continue` once you are done.
8. Enable `Event Subscriptions` and click on `Add new event subscriptions`.
9. Enter a name for this subscription (does not matter).
10. Your `Event notification endpoint URL` should be set to `<BASE_HA_URL>/api/webhook/<WEBHOOK_ID>`. Use any ID that you already aren't using in your Home Assistant instance. I generated mine using a ![GUID Generator][https://www.guidgenerator.com/]. Remember this ID for later.
11. Now click on `Add events`. From this menu, you can choose what events you want to subscribe to. For my example from earlier, you would go to the `User Activity` event type and check the box next to `User's presence status has been updated`.
12. Once you are done, click `Done`, then `Save` the subscription before hitting `Continue`.
13. The `Scopes` section should already be updated to the permissions the app would need for the events you selected earlier. Click `Continue`.
14. You are now ready to configure Home Assistant!

### Configure HomeAssistant

1. Click Install
2. Create a new top level configuration item in `configuration.yaml` as follows:
```yaml
zoom-automation:
  client_id: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
  client_secret: <CLIENT_ID_FROM_YOUR_CUSTOM_ZOOM_APP>
```
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Zoom Automation". Select it.
4. If you are not already logged into Zoom, you will be asked to log in.
5. Authorize the app for the `Scopes` that were configured earlier.
6. Start automating!

{% endif %}

> NOTE: Once your app is configured and activated, you can go back to Zoom at any time to update the events you are subscribed to. To do this, go to your ![Created Apps list][https://marketplace.zoom.us/user/build] and click on the app name. Go to the `Feature` section and expand `Event Subscriptions`. You can either edit your existing subscription and update it, which will send all of the different events through the same webhook, or create a new subscription and route it to a different webhook, your choice! Once you are done, you should check the `Scopes` section to make sure the permissions make sense for the events you selected. In my testing Zoom does a good job of updating this based on the scopes you select. Once you are done with that, you should remove the integration from the Integrations menu in the HA UI and re-add it. You may need to reauthorize the application if the scopes required have changed.

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

To see the schema of various events, check Zoom's [Webhook Reference docs][https://marketplace.zoom.us/docs/api-reference/webhook-reference]. On the left hand side navigation, you can click into the various Event types and see the format of the JSON that will be sent to your webhook.

To create a condition on an event type, use something like the following:
```
condition:
  condition: template
  value_template: '{{ trigger.json.event == "user.presence_status_updated" }}'
```

You will likely want to act on information in `trigger.json.payload.object`, either in a `condition` or an `action`. Be sure to use `value_template` and `data_template` when accessing this information in your configured automation.

<!---->

***

[zoom]: https://zoom.us/
[commits-shield]: https://img.shields.io/github/commit-activity/y/raman325/ha-zoom-automation.svg?style=for-the-badge
[commits]: https://github.com/raman325/ha-zoom-automation/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/raman325/ha-zoom-automation.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40raman325-blue
[last-commit-shield]: https://img.shields.io/github/last-commit/raman325/ha-zoom-automation?style=for-the-badge
