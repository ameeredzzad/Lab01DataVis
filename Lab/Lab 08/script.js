const svg =
d3.select("#timeline");


const width=1200;
const height=400;


const margin={
left:60,
right:60
};



const tooltip =
d3.select("#tooltip");


let dataset=[];




// LOAD CSV


d3.csv("World Important Dates.csv")

.then(data=>{


console.log(data.columns);



data.forEach(d=>{


// YEAR FIX

d.Year=parseInt(d.Year);



// HANDLE EMPTY VALUES

d["Name of Incident"] =
d["Name of Incident"] || "Unknown Event";


d.Country =
d.Country || "Unknown";


d["Type of Event"] =
d["Type of Event"] || "Unknown";


d.Outcome =
d.Outcome || "Unknown";


d.Date =
d.Date || "Unknown";



});



// REMOVE INVALID YEARS

dataset =
data.filter(
d=>!isNaN(d.Year)
);



console.log(
"Loaded events:",
dataset.length
);



createFilters();


drawTimeline(dataset);


})

.catch(error=>{

console.log(error);

alert(
"CSV file cannot be loaded"
);

});







// CREATE FILTER OPTIONS


function createFilters(){



let countries =
[
...new Set(
dataset.map(d=>d.Country)
)
];



d3.select("#countryFilter")

.selectAll("option.country")

.data(countries)

.enter()

.append("option")

.attr("class","country")

.attr("value",d=>d)

.text(d=>d);







let types =
[
...new Set(
dataset.map(d=>d["Type of Event"])
)
];



d3.select("#typeFilter")

.selectAll("option.type")

.data(types)

.enter()

.append("option")

.attr("class","type")

.attr("value",d=>d)

.text(d=>d);



}









// FILTERING


d3.selectAll(
"#search,#countryFilter,#typeFilter"
)

.on("input change",()=>{


let keyword =
d3.select("#search")
.property("value")
.toLowerCase();



let country =
d3.select("#countryFilter")
.property("value");



let type =
d3.select("#typeFilter")
.property("value");





let filtered =
dataset.filter(d=>{


return (

d["Name of Incident"]
.toLowerCase()
.includes(keyword)


&&


(country==="All" ||
d.Country===country)


&&


(type==="All" ||
d["Type of Event"]===type)


);


});



drawTimeline(filtered);



});









function drawTimeline(data){



svg.selectAll("*")
.remove();



// EMPTY DATA CHECK

if(data.length===0){


svg.append("text")

.attr("x",500)

.attr("y",200)

.text(
"No events found"
);


return;

}





// =================
// SUMMARY
// =================



d3.select("#totalEvents")
.text(data.length);



d3.select("#earliest")
.text(
d3.min(data,d=>d.Year)
);



d3.select("#latest")
.text(
d3.max(data,d=>d.Year)
);



d3.select("#countries")
.text(

new Set(
data.map(d=>d.Country)
).size

);



d3.select("#eventTypes")
.text(

new Set(
data.map(
d=>d["Type of Event"]
)
).size

);







// SCALE


let x =
d3.scaleLinear()

.domain(
[
d3.min(data,d=>d.Year),
d3.max(data,d=>d.Year)
]
)

.range(
[
margin.left,
width-margin.right
]
);







// AXIS


svg.append("line")

.attr("x1",margin.left)

.attr("x2",width-margin.right)

.attr("y1",200)

.attr("y2",200)

.attr("stroke","black")

.attr("stroke-width",2);






svg.append("g")

.attr(
"transform",
"translate(0,220)"
)

.call(
d3.axisBottom(x)
.tickFormat(d3.format("d"))
);







// COLOR


let color =
d3.scaleOrdinal()

.domain(

[
...new Set(
dataset.map(
d=>d["Type of Event"]
)
)

]

)

.range(
d3.schemeCategory10
);








// EVENT CIRCLES


svg.selectAll("circle")

.data(data)

.enter()

.append("circle")

.attr(
"cx",
d=>x(d.Year)
)


.attr(
"cy",
200
)


.attr(
"r",
8
)


.attr(
"fill",
d=>color(
d["Type of Event"]
)

)




.on(
"mouseover",
(event,d)=>{


tooltip

.style("opacity",1)

.html(

`
<b>${d["Name of Incident"]}</b>

<br><br>

Date:
${d.Date}

<br>

Year:
${d.Year}

<br>

Country:
${d.Country}

<br>

Type:
${d["Type of Event"]}

<br>

Outcome:
${d.Outcome}

`

)


.style(
"left",
event.pageX+15+"px"
)

.style(
"top",
event.pageY+15+"px"
);


}



)


.on(
"mouseout",
()=>tooltip.style("opacity",0)

);




createLegend(color);



}








// LEGEND


function createLegend(color){


d3.select("#legend")
.html("");



color.domain()
.forEach(type=>{


d3.select("#legend")

.append("div")

.attr(
"class",
"legend-item"
)

.html(

`
<span 
class="legend-color"
style="background:${color(type)}">
</span>

${type}

`

);


});


}