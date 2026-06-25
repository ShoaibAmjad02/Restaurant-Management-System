import os

base = r'C:\Users\Hp\Desktop\Restaurant Management System'
files_to_update = [
    os.path.join(base, 'megaone', 'templates', 'index.html'),
    os.path.join(base, 'megaone', 'templates', 'food-delivery', 'restaurant-detail.html'),
    os.path.join(base, 'megaone', 'templates', 'admin', 'dashboard.html'),
    os.path.join(base, 'megaone', 'templates', 'admin', 'add_product.html'),
    os.path.join(base, 'megaone', 'templates', 'admin', 'edit_product.html'),
]

replacements = {
    "{% url 'loyalty_cards:my_card' %}": "{% url 'users:loyalty_card_view' %}",
    "{% url 'loyalty_cards:download_pdf'": "{% url 'users:download_loyalty_pdf'",
    "{% url 'loyalty_cards:download_image'": "{% url 'users:download_loyalty_image'",
    "{% url 'loyalty_cards:card_data' %}": "{% url 'users:loyalty_card_data' %}",
    "{% url 'loyalty_cards:checkout_info' %}": "{% url 'users:loyalty_checkout_info' %}",
    "{% url 'loyalty_cards:admin_loyalty_list' %}": "{% url 'users:admin_loyalty_list' %}",
    "{% url 'loyalty_cards:admin_loyalty_detail'": "{% url 'users:admin_loyalty_detail'",
    "{% url 'loyalty_cards:admin_reports' %}": "{% url 'users:admin_loyalty_reports' %}",
    "{% url 'loyalty_cards:admin_export_csv' %}": "{% url 'users:admin_export_loyalty_csv' %}",
    "{% url 'loyalty_cards:admin_toggle_status'": "{% url 'users:admin_toggle_card_status'",
    "{% url 'loyalty_cards:admin_reset_points'": "{% url 'users:admin_reset_points'",
}

for fp in files_to_update:
    if not os.path.exists(fp):
        print(f'SKIP: {fp} not found')
        continue
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
    if content != original:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'UPDATED: {fp}')
    else:
        print(f'NO CHANGE: {fp}')

print('Done')
