#!/bin/bash

# Copyright (c) Huawei Technologies Co., Ltd. 2018-2019. All rights reserved.
# Description: This script uses to update docker-ce component's version and release
# Author: caihaomin@huawei.com
# Create: 2018-10-25

changeID=`git log -1 | grep Change-Id | awk '{print $2}'`
if [ "${changeID}" = "" ];then
    changeID=`date | sha256sum | head -c 40`
fi
echo "${changeID}" > git-commit

old_version=`head -n 10 docker.spec|grep Release|awk '{print $2}'`
let new_version=$old_version+1
sed  -i -e "s/^\Release: $old_version/Release: $new_version/g" ./*.spec
echo 18.09.0.$new_version > VERSION-openeuler

author=$(git config user.name)
email=$(git config user.email)
version=$(head -1 docker.spec | awk '{print $NF}')
release=$(head -10 docker.spec | grep Release | awk '{print $2}' | awk -F% '{print $1}')
new_all=$version-$release
new_changelog=$(cat << EOF
* $(LC_ALL="C" date '+%a %b %d %Y') $author<$email> - $new_all\n- Type:\n- CVE:\n- SUG:\n- DESC:\n
EOF
)
sed -i -e "/\%changelog/a$new_changelog" *.spec
