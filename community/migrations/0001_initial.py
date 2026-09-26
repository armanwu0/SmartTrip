from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='DestinationReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_name', models.CharField(max_length=200)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('visited_month', models.CharField(blank=True, max_length=20)),
                ('travel_style', models.CharField(blank=True, max_length=100)),
                ('helpful_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('user', 'destination_name')},
            },
        ),
        migrations.CreateModel(
            name='ReviewHelpful',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='helpful_votes', to='community.destinationreview')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'unique_together': {('user', 'review')},
            },
        ),
        migrations.CreateModel(
            name='TripBlog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('destination', models.CharField(max_length=200)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('content', models.TextField()),
                ('cover_emoji', models.CharField(default='✈️', max_length=10)),
                ('tags', models.CharField(blank=True, max_length=300)),
                ('likes', models.IntegerField(default=0)),
                ('views', models.IntegerField(default=0)),
                ('published', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blogs', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BlogLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked_by', to='community.tripblog')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'unique_together': {('user', 'blog')},
            },
        ),
    ]
