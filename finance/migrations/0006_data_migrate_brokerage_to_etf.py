from django.db import migrations


def map_brokerage_to_etf(apps, schema_editor):
    Account = apps.get_model('finance', 'Account')
    Account.objects.filter(type='BROKERAGE').update(type='ETF_STOCKS')


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_account_expected_return_annual_pct_and_more'),
    ]

    operations = [
        migrations.RunPython(map_brokerage_to_etf, reverse_noop),
    ]


