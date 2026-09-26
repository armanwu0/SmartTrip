from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.URLField(blank=True, default='')),
                ('bio', models.TextField(blank=True, default='')),
                ('phone', models.CharField(blank=True, default='', max_length=20)),
                ('location', models.CharField(blank=True, default='', max_length=200)),
                ('travel_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='SavedTrip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_name', models.CharField(max_length=200)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('summary', models.TextField(blank=True)),
                ('estimated_cost', models.CharField(blank=True, max_length=100)),
                ('best_time', models.CharField(blank=True, max_length=200)),
                ('trip_data', models.JSONField(default=dict)),
                ('notes', models.TextField(blank=True, default='')),
                ('is_completed', models.BooleanField(default=False)),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_trips', to='auth.user')),
            ],
            options={
                'ordering': ['-saved_at'],
            },
        ),
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_name', models.CharField(max_length=200)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist', to='auth.user')),
            ],
            options={
                'unique_together': {('user', 'destination_name')},
            },
        ),
    ]
