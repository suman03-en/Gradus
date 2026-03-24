from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("classrooms", "0005_alter_classroomtasktypeweightage_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="classroom",
            name="teachers",
            field=models.ManyToManyField(
                blank=True,
                related_name="teaching_classrooms",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
