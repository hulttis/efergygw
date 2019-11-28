#!/bin/bash
# copy to app directory (one level up from efergygw)
echo efergygw (github)
systemctl stop efergygw
rm -frv ./efergygw/new
cp -v ./efergygw/efergygw.json ./efergygw.json.bk
git clone --single-branch https://github.com/hulttis/efergygw.git efergygw/new
cp -vr ./efergygw/new/* ./efergygw/.
cp -vr efergygw.json.bk ./efergygw/efergygw.json
rm -v efergygw.json.bk
systemctl start efergygw
