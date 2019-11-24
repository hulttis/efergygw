#!/bin/bash
# copy to app directory (one level up from efergygw)
echo efergygw branch: ${1:-asyncio}
systemctl stop efergygw
rm -frv ./efergygw/new
cp -v ./efergygw/efergygw.json ./efergygw.json.bk
git clone -b ${1:-asyncio} --single-branch https://timo:tED_Frds72CcC27teW4o@git.kopsu.eu/python/efergy.git efergygw/new
cp -vr ./efergygw/new/* ./efergygw/.
cp -vr efergygw.json.bk ./efergygw/efergygw.json
systemctl start efergygw
