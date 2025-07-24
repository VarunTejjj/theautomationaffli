# config.py

BOT_TOKEN = "8301262035:AAFFdlOpGUJ2tSv84VGOmpv-I5X-EpltkSc"

# Force Join Channel
FORCE_CHANNEL_ID = -1002750966898
FORCE_CHANNEL_LINK = "https://t.me/+yefc5k-8t1oxMDFl"

# Public Product Channel (for posting updates if needed)
PUBLIC_CHANNEL_ID = -1002800054599
PUBLIC_CHANNEL_LINK = "https://t.me/anythinghere07"

# Admin user ID (Only this ID can interact for product link)
ADMIN_ID = 1831313735  # Replace with your Telegram user ID

# Adsterra script (this will be injected into Blogger post)
ADSTERRA_SCRIPT = """
<script type='text/javascript'>
	atOptions = {
		'key' : 'your-key-here',
		'format' : 'iframe',
		'height' : 250,
		'width' : 300,
		'params' : {}
	};
	document.write('<scr' + 'ipt type="text/javascript" src="https://www.profitabledisplaynetwork.com/your-script.js"></scr' + 'ipt>');
</script>
"""
