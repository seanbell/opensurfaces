import re
import os
import random
from collections import Counter

from clint.textui import progress

from django.core.management.base import BaseCommand

from photos.models import Photo


class Command(BaseCommand):
    args = ''
    help = 'Set up test/train/validation split for machine learning'

    def handle(self, *args, **options):
        if len(args) < 2:
            print 'Usage: ./manage.py split_label_images [test-fraction] [valid-fraction]'
            return

        test_frac = float(args[0])
        valid_frac = float(args[1])

        assert test_frac + valid_frac < 1.0

        local_dir = 'image-labels'

        id_usernames = []
        for filename in progress.bar(os.listdir(local_dir)):
            if not re.match(r'\d+.png', filename):
                continue
            id = int(filename.split('.')[0])
            username = Photo.objects.get(id=id).flickr_user.username
            id_usernames.append((id, username))

        test = []
        train = []
        valid = []

        # assign split by Flickr username, in decreasing order of user
        # popularity
        username_counts = Counter([x[1] for x in id_usernames]).most_common()
        for username, __ in username_counts:
            filenames = ['%s.bmp' % x[0]
                         for x in id_usernames if x[1] == username]

            tot = len(test) + len(train) + len(valid)
            if len(test) < tot * test_frac:
                test += filenames
            elif len(valid) < tot * valid_frac:
                valid += filenames
            else:
                train += filenames

        for l in (test, train, valid):
            random.shuffle(l)

        save_list(test, '%s/Test.txt' % local_dir)
        save_list(valid, '%s/Validation.txt' % local_dir)
        save_list(train, '%s/Train.txt' % local_dir)
        save_list(test + valid + train, '%s/All.txt' % local_dir)


def save_list(l, filename):
    with open(filename, 'w') as f:
        f.writelines(['%s\n' % s for s in l])
