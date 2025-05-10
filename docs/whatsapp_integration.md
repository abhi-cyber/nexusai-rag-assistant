# WhatsApp Integration Guide

This guide explains how to set up and use the WhatsApp integration with Twilio in the Dataset SQL Assistant.

## Prerequisites

1. A Twilio account (you can sign up at [twilio.com](https://www.twilio.com))
2. A WhatsApp Business Profile approved by Twilio (or use Twilio's Sandbox for testing)

## Setting up Twilio for WhatsApp

### Step 1: Create a Twilio Account

If you don't already have one, sign up for a Twilio account at [twilio.com](https://www.twilio.com).

### Step 2: Access the WhatsApp Business API

In your Twilio console, navigate to Messaging > Try it out > Send a WhatsApp message.

### Step 3: Set Up a WhatsApp Sender

For testing, you can use the Twilio Sandbox for WhatsApp, which provides a temporary WhatsApp number.

For production:

1. Request access to the WhatsApp Business API through Twilio
2. Register your WhatsApp Business Profile
3. Get your approved WhatsApp sender number

### Step 4: Configure Webhooks

To receive incoming WhatsApp messages, you need to configure a webhook:

1. Deploy your application to a server with a public URL
2. Run the webhook.py Flask application
3. In your Twilio console, go to Messaging > Settings > WhatsApp Sandbox Settings
4. Set the "When a message comes in" URL to your webhook endpoint (https://your-domain.com/webhook)

## Configuring the Application

1. Go to the "WhatsApp Integration" tab in the application
2. Enter your Twilio Account SID and Auth Token (found in your Twilio Console dashboard)
3. Enter your WhatsApp number (with country code, e.g., +14155238886)
4. Click "Test Twilio Connection" to verify your credentials

## Using the WhatsApp Integration

### Sending Messages

You can send WhatsApp messages directly from the application:

1. Go to the "WhatsApp Integration" tab
2. Enter the recipient's phone number with country code
3. Type your message
4. Click "Send WhatsApp Message"

### Receiving and Processing Messages

When someone sends a message to your WhatsApp number:

1. Twilio forwards the message to your webhook
2. The webhook processes the message using the SQL and/or Jira agents
3. A response is automatically sent back to the user via WhatsApp

## Troubleshooting

### Message Not Sending

- Verify your Twilio credentials are correct
- Make sure the recipient number is in the correct format (e.g., +14155238886)
- Check that you have enough Twilio credit

### Not Receiving Messages

- Ensure your webhook URL is correctly set in the Twilio console
- Verify the webhook server is running and accessible
- Check that the `/webhook` endpoint is correctly handling POST requests

### Using ngrok for Local Development

If you're developing locally, you can use ngrok to create a public URL for your webhook:
