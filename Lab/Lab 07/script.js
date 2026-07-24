const margin =
{
top:40,
right:40,
bottom:60,
left:80
};



let dataset=[];



const tooltip=d3.select("#tooltip")
.attr("class","tooltip")
.style("opacity",0);



d3.csv("Walmart_Sales.csv")
.then(data=>{


data.forEach(d=>{


d.Store=+d.Store;

d.Weekly_Sales=+d.Weekly_Sales;

d.Holiday_Flag=+d.Holiday_Flag;

d.Temperature=+d.Temperature;

d.Fuel_Price=+d.Fuel_Price;

d.CPI=+d.CPI;

d.Unemployment=+d.Unemployment;


d.Date=d3.timeParse("%d-%m-%Y")(d.Date);


// Extract year

d.Year=d.Date.getFullYear();



});


dataset=data;



createStoreFilter();

createYearFilter();


drawAll(data);



});




// FILTER


function createStoreFilter(){


let stores=
[...new Set(dataset.map(d=>d.Store))];


d3.select("#storeFilter")

.selectAll("option.store")

.data(stores)

.enter()

.append("option")

.attr("class","store")

.attr("value",d=>d)

.text(d=>"Store "+d);



}

function createYearFilter(){


let years =
[
...new Set(
dataset.map(d=>d.Year)
)

];



d3.select("#yearFilter")

.selectAll("option.year")

.data(years)

.enter()

.append("option")

.attr(
"class",
"year"
)

.attr(
"value",
d=>d
)

.text(d=>d);



}


d3.select("#applyFilter")

.on("click",()=>{


let store =
d3.select("#storeFilter")
.property("value");



let holiday =
d3.select("#holidayFilter")
.property("value");



let year =
d3.select("#yearFilter")
.property("value");



let minSales =
+d3.select("#minSales")
.property("value");



let maxSales =
+d3.select("#maxSales")
.property("value");





let filtered = dataset.filter(d=>{


let storeMatch =
store==="All" ||
d.Store==store;



let holidayMatch =
holiday==="All" ||
d.Holiday_Flag==holiday;




let yearMatch =
year==="All" ||
d.Year==year;




let minMatch =
!minSales ||
d.Weekly_Sales>=minSales;



let maxMatch =
!maxSales ||
d.Weekly_Sales<=maxSales;




return (

storeMatch &&
holidayMatch &&
yearMatch &&
minMatch &&
maxMatch

);



});




drawAll(filtered);

});



function drawAll(data){


drawLine(data);

drawBar(data);

drawDonut(data);

drawScatter(data);


}





// ---------------- LINE CHART ----------------


function drawLine(data){



d3.select("#lineChart").selectAll("*").remove();



let svg=d3.select("#lineChart");



let width=800-margin.left-margin.right;

let height=400-margin.top-margin.bottom;



let g=svg.append("g")

.attr("transform",
`translate(${margin.left},${margin.top})`);




let x=d3.scaleTime()

.domain(d3.extent(data,d=>d.Date))

.range([0,width]);



let y=d3.scaleLinear()

.domain([0,d3.max(data,d=>d.Weekly_Sales)])

.range([height,0]);




g.append("g")

.attr("transform",
`translate(0,${height})`)

.call(d3.axisBottom(x));



g.append("g")

.call(d3.axisLeft(y));




let line=d3.line()

.x(d=>x(d.Date))

.y(d=>y(d.Weekly_Sales));



g.append("path")

.datum(data)

.attr("fill","none")

.attr("stroke","steelblue")

.attr("stroke-width",2)

.attr("d",line);





g.selectAll("circle")

.data(data)

.enter()

.append("circle")

.attr("cx",d=>x(d.Date))

.attr("cy",d=>y(d.Weekly_Sales))

.attr("r",4)

.attr("fill","orange")



.on("mouseover",(event,d)=>{


tooltip

.style("opacity",1)

.html(

`
Date: ${d.Date.toDateString()}
<br>
Sales: $${d.Weekly_Sales.toLocaleString()}
`

)

.style("left",
event.pageX+"px")

.style("top",
event.pageY+"px");


})


.on("mouseout",
()=>tooltip.style("opacity",0));



}





// ---------------- BAR CHART ----------------

function drawBar(data){

    d3.select("#barChart")
    .selectAll("*")
    .remove();


    let svg = d3.select("#barChart");


    let grouped = d3.rollups(
        data,
        v => d3.sum(v, d => d.Weekly_Sales),
        d => d.Store
    )
    .map(d => ({
        store: d[0],
        sales: d[1]
    }));


    // Sort store based on sales
    grouped.sort((a,b)=>b.sales-a.sales);



    let width = 700 - margin.left - margin.right;
    let height = 400 - margin.top - margin.bottom;



    let g = svg.append("g")
    .attr(
        "transform",
        `translate(${margin.left},${margin.top})`
    );



    // X axis - Store number

    let x = d3.scaleBand()

    .domain(grouped.map(d=>d.store))

    .range([0,width])

    .padding(0.2);



    // Y axis - Total Sales

    let y = d3.scaleLinear()

    .domain([
        0,
        d3.max(grouped,d=>d.sales)
    ])

    .nice()

    .range([height,0]);




    // Axes

    g.append("g")

    .attr(
        "transform",
        `translate(0,${height})`
    )

    .call(d3.axisBottom(x));



    g.append("g")

    .call(

        d3.axisLeft(y)

        .tickFormat(d=>"$"+(d/1000000).toFixed(1)+"M")

    );




    // Find highest performing store

    let topStore =
    d3.max(grouped,d=>d.sales);





    // Draw Bars

    g.selectAll("rect")

    .data(grouped)

    .enter()

    .append("rect")

    .attr(
        "x",
        d=>x(d.store)
    )

    .attr(
        "y",
        d=>y(d.sales)
    )

    .attr(
        "width",
        x.bandwidth()
    )

    .attr(
        "height",
        d=>height-y(d.sales)
    )


    // Highlight top store

    .attr(
        "fill",
        d=>d.sales===topStore
        ? "crimson"
        : "steelblue"
    )



    // Tooltip

    .on("mouseover",(event,d)=>{


        tooltip

        .style("opacity",1)

        .html(

        `
        <b>Store:</b> ${d.store}
        <br>
        <b>Total Sales:</b>
        $${d.sales.toLocaleString()}
        `

        )


        .style(
            "left",
            event.pageX+"px"
        )

        .style(
            "top",
            event.pageY+"px"
        );


    })


    .on(
        "mouseout",
        ()=>tooltip.style("opacity",0)
    );





    // Add label for top store

    let top =
    grouped.find(
        d=>d.sales===topStore
    );


    g.append("text")

    .attr(
        "x",
        x(top.store)+x.bandwidth()/2
    )

    .attr(
        "y",
        y(top.sales)-10
    )

    .attr(
        "text-anchor",
        "middle"
    )

    .style(
        "font-size",
        "12px"
    )

    .style(
        "font-weight",
        "bold"
    )

    .text(
        "Top Store"
    );


}




// ---------------- DONUT ----------------


function drawDonut(data){



d3.select("#donutChart")
.selectAll("*")
.remove();



let svg=d3.select("#donutChart");



let values=[

{
name:"Holiday Week",
value:d3.sum(
data.filter(d=>d.Holiday_Flag==1),
d=>d.Weekly_Sales)
},


{
name:"Non-Holiday Week",
value:d3.sum(
data.filter(d=>d.Holiday_Flag==0),
d=>d.Weekly_Sales)
}

];




let pie=d3.pie()

.value(d=>d.value);



let arc=d3.arc()

.innerRadius(70)

.outerRadius(130);



let g=svg.append("g")

.attr("transform","translate(250,200)");




let color=d3.scaleOrdinal()

.range(["orange","steelblue"]);




g.selectAll("path")

.data(pie(values))

.enter()

.append("path")

.attr("d",arc)

.attr("fill",d=>color(d.data.name));





g.selectAll("text")

.data(pie(values))

.enter()

.append("text")

.attr("transform",
d=>`translate(${arc.centroid(d)})`)

.text(d=>

d.data.name

);



}




// ---------------- SCATTER ----------------


function drawScatter(data){


d3.select("#scatterPlot")
.selectAll("*")
.remove();



let svg=d3.select("#scatterPlot");



let width=700-margin.left-margin.right;

let height=400-margin.top-margin.bottom;



let g=svg.append("g")

.attr("transform",
`translate(${margin.left},${margin.top})`);




let x=d3.scaleLinear()

.domain(d3.extent(data,d=>d.Fuel_Price))

.range([0,width]);



let y=d3.scaleLinear()

.domain([0,d3.max(data,d=>d.Weekly_Sales)])

.range([height,0]);




g.append("g")

.attr("transform",
`translate(0,${height})`)

.call(d3.axisBottom(x));



g.append("g")

.call(d3.axisLeft(y));




g.selectAll("circle")

.data(data)

.enter()

.append("circle")

.attr("cx",d=>x(d.Fuel_Price))

.attr("cy",d=>y(d.Weekly_Sales))

.attr("r",5)

.attr("fill",

d=>d.Holiday_Flag?
"red":
"steelblue"

)



.on("mouseover",(event,d)=>{


tooltip.style("opacity",1)

.html(

`
Store: ${d.Store}
<br>
Fuel Price: ${d.Fuel_Price}
<br>
Sales: $${d.Weekly_Sales.toLocaleString()}
`

)

.style("left",event.pageX+"px")

.style("top",event.pageY+"px");


})


.on("mouseout",
()=>tooltip.style("opacity",0));



}