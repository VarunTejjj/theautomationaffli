# utils.py

ADSTERRA_SCRIPT = """
<!-- Adsterra Ad Code -->
<script type="text/javascript">
   atOptions = {
      'key' : 'your_adsterra_key_here',
      'format' : 'iframe',
      'height' : 250,
      'width' : 300,
      'params' : {}
   };
   document.write('<scr' + 'ipt type="text/javascript" src="https://www.profitabledisplaynetwork.com/' + atOptions.key + '/invoke.js"></scr' + 'ipt>');
</script>
"""

def generate_post_content(product_link):
    return f"""
    <div>
        <h2>🔥 Grab Your Product Now!</h2>
        <p>Click the button below to access the original product link:</p>
        <a href="{product_link}" target="_blank" style="padding: 10px 20px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px;">View Product</a>
        <br><br>
        {ADSTERRA_SCRIPT}
        <p>Stay tuned for more amazing deals!</p>
    </div>
    """
