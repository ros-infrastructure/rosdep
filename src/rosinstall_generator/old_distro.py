import rospkg.distro as rosdistro
import yaml


def generate_dry_rosinstall(distro_name, variant):
    # Parse distro file
    distro_obj = rosdistro.load_distro(rosdistro.distro_uri(distro_name))

    rosinstall = rosdistro.distro_to_rosinstall(distro_obj, 'release-tar',
                                                variant_name=variant)
    return yaml.safe_dump(rosinstall, default_flow_style=False)
