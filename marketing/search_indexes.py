from haystack import indexes
from marketing.models import Contact, FailedContact


class MarketingContactIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(
        document=True, use_template=True, template_name='search/contact_emails.txt')

    id = indexes.CharField(model_attr='id')
    email = indexes.EdgeNgramField(model_attr='email')
    email_domain = indexes.EdgeNgramField()
    name = indexes.CharField(model_attr='name')
    company_name = indexes.CharField()
    created_on = indexes.CharField(model_attr='created_on')
    created_on_arrow = indexes.CharField(model_attr='created_on_arrow')
    created_by = indexes.CharField()
    created_by_id = indexes.CharField()
    contact_lists = indexes.MultiValueField()
    contact_lists_id = indexes.MultiValueField()
    contact_lists_name = indexes.MultiValueField()
    is_bounced = indexes.BooleanField()
    contact_lists_count = indexes.IntegerField()

    def get_model(self):
        return Contact

    def prepare_email_domain(self, obj):
        return obj.email.split('@')[-1]

    def prepare_contact_lists(self, obj):
        return [[contact_list.id, contact_list.name if contact_list.name else ''] for contact_list in obj.contact_list.all()]

    def prepare_contact_lists_id(self, obj):
        return [contact_list.id for contact_list in obj.contact_list.all().order_by('id')]

    def prepare_contact_lists_name(self, obj):
        return [contact_list.name for contact_list in obj.contact_list.all().order_by('id')]

    def prepare_company_name(self, obj):
        return obj.company_name if obj.company_name else ''

    def prepare_created_by(self, obj):
        return obj.created_by.email if obj.created_by else ''

    def prepare_created_by_id(self, obj):
        return obj.created_by.id if obj.created_by else ''

    def prepare_is_bounced(self, obj):
        return obj.is_bounced

    def prepare_contact_lists_count(self, obj):
        return obj.contact_list.count()

    def index_queryset(self, using=None):
        return self.get_model().objects.all()



class MarketingFailedContactIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(
        document=True, use_template=True, template_name='search/failed_contact_emails.txt')

    id = indexes.CharField(model_attr='id')
    email = indexes.EdgeNgramField(model_attr='email')
    email_domain = indexes.EdgeNgramField()
    name = indexes.CharField(model_attr='name')
    company_name = indexes.CharField()
    created_on = indexes.CharField(model_attr='created_on')
    created_on_arrow = indexes.CharField(model_attr='created_on_arrow')
    created_by = indexes.CharField()
    created_by_id = indexes.CharField()
    contact_lists = indexes.MultiValueField()
    contact_lists_id = indexes.MultiValueField()
    contact_lists_name = indexes.MultiValueField()
    contact_lists_count = indexes.IntegerField()


    def get_model(self):
        return FailedContact

    def prepare_email_domain(self, obj):
        return obj.email.split('@')[-1]

    def prepare_contact_lists(self, obj):
        return [[contact_list.id, contact_list.name if contact_list.name else ''] for contact_list in obj.contact_list.all()]

    def prepare_contact_lists_id(self, obj):
        return [contact_list.id for contact_list in obj.contact_list.all().order_by('id')]

    def prepare_contact_lists_name(self, obj):
        return [contact_list.name for contact_list in obj.contact_list.all().order_by('id')]

    def prepare_company_name(self, obj):
        return obj.company_name if obj.company_name else ''

    def prepare_created_by(self, obj):
        return obj.created_by.email if obj.created_by else ''

    def prepare_created_by_id(self, obj):
        return obj.created_by.id if obj.created_by else ''

    def prepare_contact_lists_count(self, obj):
        return obj.contact_list.count()

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
