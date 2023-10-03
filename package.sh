#!/bin/sh

if [ ! -d $1 ]; then
    echo "$1 does not exist" >&2
    exit 1
fi

pushd $1

if [ -d package ]; then
    rm -fr package
fi

if [ -e package.zip ]; then
    rm package.zip
fi

mkdir package
pip3 install --target ./package line-bot-sdk
pushd package
zip -r ../package.zip .
popd
zip package.zip lambda_function.py
aws s3api put-object --bucket skgw-lambda-trigger-test --key $1/package.zip --body package.zip
popd
