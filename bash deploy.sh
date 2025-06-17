#!/bin/bash

echo "== Budowanie frontendu =="
cd frontend
npm install
npm run build

echo "== Czyszczenie starego builda w backend/static =="
rm -rf ../backend/static/*

echo "== Kopiowanie nowego builda do backend/static =="
cp -r build/* ../backend/static/

echo "== Gotowe! =="
