"""Restore verified migrated environments to fast ephemeral disk after a restart."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=Path('/workspace/t47d_public_migration.tar.gz'))
    parser.add_argument('--runtime-root',type=Path,default=Path('/tmp/t47d_preflight_runtime'))
    args=parser.parse_args()
    expected='b7509b246a2f130912d0b327ef8d65df2c69b8811f707ba0fe2eba9eeb49bdd2'
    with args.archive.open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=expected:
        raise RuntimeError('Migration archive checksum mismatch; do not restore')
    names=['t47d_full_venv','t47d_tf_venv','t47d_r']
    for name in names:
        link=Path('/workspace')/name
        if link.exists() and not link.is_symlink():
            raise RuntimeError('Preserve or move existing directory before linking: '+str(link))
    args.runtime_root.mkdir(parents=True,exist_ok=True)
    subprocess.run(['tar','--no-same-owner','-xzf',str(args.archive),'-C',str(args.runtime_root),*names],check=True)
    for name in names:
        link=Path('/workspace')/name
        destination=(args.runtime_root/name).resolve()
        if link.is_symlink():
            if link.resolve()!=destination:
                raise RuntimeError('Unexpected existing environment link: '+str(link))
        else:
            link.symlink_to(destination,target_is_directory=True)
    print(json.dumps({'restored':names,'archive_sha256':actual,'runtime_root':str(args.runtime_root),
        'persistent_copy':'Network Volume archive; datasets and results stay under /workspace/vc-demo'}))


if __name__=='__main__':
    main()
