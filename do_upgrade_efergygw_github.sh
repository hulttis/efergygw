#!/bin/bash
# copy to app directory (one level up from efergygw)
echo "efergygw (github)"
systemctl stop efergygw
rm -frv ./efergygw/new
cp -v ./efergygw/efergygw.json ./efergygw.json.upg
git clone --single-branch https://github.com/hulttis/efergygw.git efergygw/new
cp -vr ./efergygw/new/* ./efergygw/.
cp -vr efergygw.json.upg ./efergygw/efergygw.json
rm -v efergygw.json.upg
systemctl start efergygw
echo "efegygw (github) upgrade done"
