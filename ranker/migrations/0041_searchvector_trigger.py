from django.db import migrations
from django.contrib.postgres.search import SearchVector

def compute_search_vector(apps, schema_editor):
    Answer = apps.get_model("ranker", "Answer")
    Answer.objects.update(search_vector=SearchVector('answer'))

class Migration(migrations.Migration):
    dependencies = [
        ("ranker", "0040_answer"),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
              CREATE TRIGGER search_vector_trigger
              BEFORE INSERT OR UPDATE OF answer, search_vector
              ON ranker_answer
              FOR EACH ROW EXECUTE PROCEDURE
              tsvector_update_trigger(
                search_vector, 'pg_catalog.english', answer
              );
            ''',

            reverse_sql = '''
              DROP TRIGGER IF EXISTS search_vector_trigger
              ON ranker_keyword;
            '''
        ),
        migrations.RunPython(
            compute_search_vector, reverse_code=migrations.RunPython.noop
        ),
    ]
