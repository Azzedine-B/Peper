function table_to_csv(source) {
    var data = source.data;
    const tabl = Object.keys(data);
    
    if (tabl[0] == 'index'){
        var debut = 1;
        }
    else{
        var debut=0;
        }
    
    var filetext = tabl[debut];
    for (i=debut+1; i < tabl.length; i++){
        filetext=filetext.concat(',',tabl[i]);
    }
    filetext=filetext.concat('\n');
   
    for (i=0; i < data[tabl[debut]].length; i++) {
        var currRow = [data[tabl[debut]][i].toString()]
        for(j=debut+1; j < tabl.length-1; j++){
            currRow.push(data[tabl[j]][i].toString());
        }
        currRow.push(data[tabl[j]][i].toString().concat('\n'));
        var joined = currRow.join();
        filetext = filetext.concat(joined);
    }
    return filetext
}

var filename = 'data.csv';
filetext = table_to_csv(source)
var blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });

//addresses IE
if (navigator.msSaveBlob) {
    navigator.msSaveBlob(blob, filename);
}

else {
    var link = document.createElement("a");
    link = document.createElement('a')
    link.href = URL.createObjectURL(blob);
    link.download = filename
    link.target = "_blank";
    link.style.visibility = 'hidden';
    link.dispatchEvent(new MouseEvent('click'))
}
