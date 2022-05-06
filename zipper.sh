folder_name=$1
zip_name=$2
rm ${zip_name}
cd $folder_name
zip -r -D ../${zip_name} *