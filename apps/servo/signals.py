from django.db import transaction


def extract_hash_tags(s):
    return set(part[1:] for part in s.split() if part.startswith('#'))


@transaction.atomic
def need_save_handler(sender, instance, created, **kwargs):
    hashtags = list(extract_hash_tags(instance.description))
    tags = ','.join(f'{w}'.format(w) for w in hashtags)
    instance.tags.set(tags)


@transaction.atomic()
def listing_member_save_handler(sender, instance, created, **kwargs):
    if instance.is_current == True:
        # Each member can active on one listing
        # member can select current listing
        cls = instance.__class__
        members = cls.objects \
            .filter(is_current=True, user_id=instance.user.id) \
            .exclude(uuid=instance.uuid)

        if members.exists():
            members.update(is_current=False)
