import os
import tempfile
import shutil


from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
from django.db import transaction
from django.contrib.auth.models import User

from licenses.models import License
from photos.add import add_photo
from common.utils import progress_bar, md5sum
from intrinsic.models import IntrinsicSyntheticDecomposition
from intrinsic.synthetic import open_multilayer_exr, \
    update_synthetic_diff_intensity


class Command(BaseCommand):
    args = ''

    def handle(self, *args, **options):
        admin_user = User.objects.get_or_create(
            username='admin')[0].get_profile()

        for filename in progress_bar(args):
            if not os.path.exists(filename):
                raise ValueError("File does not exist: '%s'" % filename)

            blendswap_id = os.path.basename(filename).split('_')[0]
            license, scene_url, scene_artist = \
                License.get_for_blendswap_scene(blendswap_id)

            print 'file:', filename
            print 'license:', license
            print 'url:', scene_url
            print 'artist:', scene_artist

            tmpdir = tempfile.mkdtemp()
            try:
                print "Loading %s..." % filename
                md5 = md5sum(filename)
                if IntrinsicSyntheticDecomposition.objects.filter(md5=md5).exists():
                    print "Already added: %s" % filename
                    continue

                multilayer = open_multilayer_exr(
                    filename, tonemap=True, thumb_size=512, show_progress=True)
                paths = {}
                for key, img in multilayer.iteritems():
                    path = os.path.join(tmpdir, '%s-%s.jpg' % (md5, key))
                    img.save(path)
                    paths[key] = path

                with transaction.atomic():
                    photo = add_photo(
                        path=paths["combined"],
                        user=admin_user,
                        license=license,
                        synthetic=True,
                        whitebalanced=True,
                        inappropriate=False,
                        nonperspective=False,
                        stylized=False,
                        rotated=False,
                    )

                    print "Uploading layers: %s..." % paths.keys()
                    IntrinsicSyntheticDecomposition.objects.create(
                        photo=photo,
                        multilayer_exr=ImageFile(open(filename, 'rb')),
                        scene_artist=scene_artist,
                        scene_url=scene_url,
                        md5=md5,
                        **{
                            ("%s_thumb" % key): ImageFile(open(path, 'rb'))
                            for key, path in paths.iteritems()
                            if key != "combined"
                        }
                    )
            finally:
                shutil.rmtree(tmpdir)

        update_synthetic_diff_intensity()
