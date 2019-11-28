#!/bin/bash
# copy to app directory (one level up from efergygw)
echo efergygw 
systemctl stop efergygw
rm -frv ./efergygw/new
git clone https://github.com/hulttis/efergygw.git efergygw/new
cp -vr ./efergygw/new/* ./efergygw/.
cp -vr efergygw.json ./efergygw/.
systemctl start efergygw
