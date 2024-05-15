# Generated by Django 4.0.2 on 2022-02-26 11:50

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtendedUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('tu_id', models.CharField(blank=True, max_length=10, null=True, verbose_name='TU-ID')),
                ('matr_nr', models.IntegerField(blank=True, null=True, verbose_name='Matriculation number')),
                ('role', models.IntegerField(choices=[(0, 'Internal Student'), (1, 'External Student'), (2, 'External Customer')], default=1, verbose_name='Role')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Billing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_billed', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LasercutMinutePrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.IntegerField(choices=[(0, 'Internal Student'), (1, 'External Student'), (2, 'External Customer')])),
                ('price_per_minute', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('default_length', models.IntegerField()),
                ('default_width', models.IntegerField()),
                ('is_fixed_size', models.BooleanField()),
                ('is_material_available', models.BooleanField(default=True)),
                ('needs_comment', models.BooleanField(default=False)),
                ('material_tooltip', models.TextField(blank=True, default='')),
                ('previewImage', models.ImageField(blank=True, null=True, upload_to='preview_images/')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MaterialVariation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thickness', models.FloatField()),
                ('price', models.IntegerField()),
                ('non_default_length', models.IntegerField(blank=True, null=True)),
                ('non_default_width', models.IntegerField(blank=True, null=True)),
                ('is_lasercutable', models.BooleanField()),
                ('is_variation_available', models.BooleanField(default=True)),
                ('base', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='model.material')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_ordered', models.DateTimeField(default=django.utils.timezone.now)),
                ('state', models.IntegerField(blank=True, choices=[(0, 'Submitted'), (1, 'In Progress'), (2, 'Awaiting Reply'), (3, 'Ready For Pickup'), (4, 'Finished'), (5, 'Billed')], default=None, null=True)),
                ('staff_comment', models.TextField(blank=True, default='')),
                ('is_rechnung', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubOrderLaserCut',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_override', models.IntegerField(blank=True, null=True)),
                ('price_billed', models.IntegerField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('customer_comment', models.TextField(blank=True, default='')),
                ('file', models.FileField(blank=True, null=True, upload_to=model.models.lasercut_file_location)),
                ('upload_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('minutes', models.IntegerField(default=0)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.order')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkshopInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descriptor', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubOrderMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_override', models.IntegerField(blank=True, null=True)),
                ('price_billed', models.IntegerField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('customer_comment', models.TextField(blank=True, default='')),
                ('amount', models.IntegerField()),
                ('size_length', models.IntegerField()),
                ('size_width', models.IntegerField()),
                ('associated_lasercut', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parts', to='model.suborderlasercut')),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='+', to='model.materialvariation')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.order')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('date_sent', models.DateTimeField(default=django.utils.timezone.now)),
                ('new_message', models.BooleanField(default=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.order')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BillingOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('billing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='model.billing')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='model.order')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]