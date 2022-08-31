function getDateDifferenceInSecs(date1, date2) {
    return (date1.getTime() - date2.getTime()) / 1000;
}


function plotSizes(sizes) {
    let sizes_times = []
    let sizes_values = []
    console.log(sizes);
    for (let dt in sizes) {
        sizes_times.push(dt);
        sizes_values.push(sizes[dt]["path_size"]);

    }


    let plotlyData = [
        {
            x: sizes_times,
            y: sizes_values,
            type: 'scatter',
            yaxis: 'y2'
        }
    ];
    return {
        "plotlyData": plotlyData,
    };







}