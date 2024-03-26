class Element {
    constructor(design, text) {
        this.div = document.createElement("div");
        this.apply_design(design);
        this.children = [];
        if(text) this.text = text;
    }

    appendChild(element, is_element=true) {
        if(is_element) this.div.appendChild(element.div);
        else this.div.appendChild(element)
        this.children.push(element);
    }

    get text()  {return this.div.innerHTML;}
    set text(v) {this.div.innerHTML = v;}
    show() {
        if(!this.on_screen()) {
            document.body.appendChild(this.div);
            this.div.style.opacity = "1";
        }
    }

    on_screen(node = this.div) {
        if(node.parentNode) {
            let a = node.parentNode === document.body;
            return a || this.on_screen(node.parentNode);
        }
        return false;
    }

    apply_design(design) {
        for(let i in design) {
            this.div.style[i] = design[i];
        }
    }
}

let send_request = (method, url, data) => {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onload = function () {
            if (xhr.status >= 200 && xhr.status < 300) {
                let responseData;
                try {
                    responseData = JSON.parse(xhr.response);
                } catch (error) {
                    // reject("Invalid JSON response");
                    // return;
                    responseData = xhr.response;
                }
                resolve(responseData);
            } else {
                reject(xhr.statusText);
            }
        };


        xhr.onerror = function () {
            reject(xhr.statusText);
        };

        // Convert data to JSON string if it's provided
        const body = data ? JSON.stringify(data) : null;

        xhr.send(body);
    });
}




/***************************************** Basic Structure Containers ***************************************/

// Contains the webpage header and some information and instructions - HC
let header_container = new Element({}, "Inductive Miner Life-cycle extension");

// Buttons and other interactive elements to start/pause/stop a selectable process (amount) and its updating - IBC
let interaction_buttons_container = new Element({}, "");

// The SVG-Graph container and info on selected elements, interactive buttons below (save/select/deselect, etc.) - GIBC
let graph_information_buttons_container = new Element({}, "");

// A live overview of currently mined traces - TDC
let traces_display_container = new Element({}, "");


/***************************************** HC ************************************************/
header_container.apply_design({
    fontWeight: "bolder",
    fontSize: "2.5em",
    width: "100vw",
    // width: "calc(100vw - 40px)",
    textAlign: "center",
    margin: "20px 0 20px 0",
    border: "0px solid red"
});


/***************************************** IBC ***********************************************/

interaction_buttons_container.apply_design({
    width: "calc(100vw - 40px)",
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    margin: "20px 0 20px 0",
    // height: "10vh",
    border: "0px solid red"
});


// Process Selector and label
let process_selector_container = new Element({
    border: "0px solid red",
}, "");

let process_selector_label = document.createElement("label");
process_selector_label.textContent = "Choose a process and how many instances to run: ";
process_selector_label.style.fontSize = "1.2em"
process_selector_label.setAttribute("for", "processes");


let process_names = ["TUM-Pra-WS-23-Discovery1", "TUM-Benzin-Pra-WS-23-2", "TUM-Benzin-Pra-WS-23-3", "Coopis 2010"];
let process_selector = document.createElement("select");
process_selector.id = "processes";
process_selector.style.margin = "10px";
process_selector.style.fontSize = "0.9em";

process_names.forEach(process_name => {
    let option = document.createElement("option");
    option.value = process_name;  // used process_name
    option.textContent = process_name;  // displayed process name
    if (process_name === process_names[3]) option.selected = true;
    process_selector.appendChild(option);
});

// Create label element for the second selector
let process_amount_label = document.createElement("label");
process_amount_label.setAttribute("for", "process_amount_input");
process_amount_label.textContent = "Enter a numeric value (1-100):";

// Create input element for numeric values
let process_amount_input = document.createElement("input");
process_amount_input.style.margin = "10px";
process_amount_input.style.width = "3em";
process_amount_input.id = "process_amount_input";
process_amount_input.type = "number";
process_amount_input.value = "0";
process_amount_input.addEventListener("input", () => {
    let value = parseInt(process_amount_input.value);
    if (isNaN(value) || value < 0) {
        process_amount_input.value = "0";
    } else if (value > 100) {
        process_amount_input.value = "100";
    }
});



// Update Mode selector and label
let selected_update_mode;
let update_mode_selector_container = new Element({
    border: "0px solid red",
}, "");

let updated_mode_selector_label = document.createElement("label");
updated_mode_selector_label.textContent = "Choose your update mode: ";
updated_mode_selector_label.style.fontSize = "1.2em"
updated_mode_selector_label.setAttribute("for", "update_modes");


let update_modes = ["Time interval", "Event-based"];
let update_mode_selector = document.createElement("select");
update_mode_selector.id = "update_modes";
update_mode_selector.style.margin = "0 22px 0 5px";
update_mode_selector.style.fontSize = "0.9em";

update_mode_selector.addEventListener("change", () => {
    if (update_mode_selector.value === update_modes[0]) {
        update_mode_event_label.textContent = "Enter the update interval in ms: "
        update_mode_event_amount_input.value = "2500";
    }
    if (update_mode_selector.value === update_modes[1]) {
        update_mode_event_label.textContent = "Enter event update batch-size: "
        update_mode_event_amount_input.value = "1";
    }
});

update_modes.forEach(update_mode => {
    let option = document.createElement("option");
    option.value = update_mode;  // used process_name
    option.textContent = update_mode;  // displayed process name
    if (update_mode === update_modes[0]) option.selected = true;
    update_mode_selector.appendChild(option);
});

// Create label element for the second selector
let update_mode_event_label = document.createElement("label");
update_mode_event_label.setAttribute("for", "update_mode_event_amount_input");
update_mode_event_label.textContent = "Enter the update interval in ms: "
update_mode_event_label.style.marginLeft = "10px";
update_mode_event_label.style.fontSize = "1.2em";

// Create input element for numeric values
let update_mode_event_amount_input = document.createElement("input");
update_mode_event_amount_input.style.margin = "10px";
update_mode_event_amount_input.style.width = "4em";
update_mode_event_amount_input.id = "update_mode_event_amount_input";
update_mode_event_amount_input.type = "number";
update_mode_event_amount_input.value = "2500";
update_mode_event_amount_input.addEventListener("input", () => {
    let value = parseInt(update_mode_event_amount_input.value);
    if (isNaN(value) || value <= 0) {
        update_mode_event_amount_input.value = "1";
    }
});



let refresh_download_button = () => {
    svg = graph_container.div.querySelector("svg");
    let created = export_button;
    let parent = graph_container;

    let new_button = get_svg_export_button(svg);
    // new_button.style.border = "0px solid red";
    new_button.style.position = "absolute";
    new_button.style.bottom = "0";
    new_button.style.right = "0";
    new_button.style.fontSize = "1.2em";
    new_button.addEventListener('mouseover', () => {
      new_button.style.backgroundColor = 'rgba(0,0,0,0)';
    }); new_button.addEventListener('mouseout', () => {
      new_button.style.backgroundColor = '';
    });


    if(!created) {
        export_button = new_button
        parent.appendChild(export_button, false)
        // export_button.addEventListener("click", () => {interaction_buttons_container.removeChild(export_button)})
    } else {
        // parent.div.removeChild(export_button);
        export_button = new_button
        parent.appendChild(export_button, false)
    }
};


let process_submit_button = document.createElement("button");
let export_button = null;
process_submit_button.style.margin = "10px";
process_submit_button.textContent = "Run";

// SUBMIT BUTTON (RUN)

process_submit_button.addEventListener("click", () => {
    graph_information_buttons_container.appendChild(graph_container);

    if (update_interval) clearInterval(update_interval);
    process_submit_button.disabled = true;
    selection.old_process = selection.process_name;
    selection.process_name = process_selector.value;
    selection.process_amount = parseInt(process_amount_input.value);
    process_amount_input.value = "0";
    instance_status = {};
    selection.svg_node = null;
    selection.node_selector = null;


    // start processes
    send_request("POST", "start_process_instances", {
        process_name: selection.process_name,
        amount: selection.process_amount
    }).then(_ => {
        console.log(`Running process "${selection.process_name}" ${selection.process_amount} time${selection.process_amount === 1? "": "s"}...`)
        // console.log(r.message);
    });




    // start update mode
    selected_update_mode = update_mode_selector.value;

    if (selected_update_mode === update_modes[0]) {  // interval-based
    update_interval_function();  // initial update
        update_interval = setInterval(update_interval_function, parseInt(update_mode_event_amount_input.value));
    } else if (selected_update_mode === update_modes[1]) {
        batch_size = parseInt(update_mode_event_amount_input.value);
        start_event_listener();
    }

    stop_update_interval_button.disabled = false;
});


let stop_updating = () => {
    if (selected_update_mode === update_modes[0]) {
        if (update_interval) {
            clearInterval(update_interval);
        }
    } else if (selected_update_mode === update_modes[1]) {
        stop_event_listener();
    }

    stop_update_interval_button.disabled = true;
    process_submit_button.disabled = false;
};

let stop_update_interval_button = document.createElement("button");
stop_update_interval_button.style.margin = "10px";
stop_update_interval_button.textContent = "Stop";
stop_update_interval_button.disabled = true;
stop_update_interval_button.addEventListener("click", stop_updating);

let clear_all_logs_button = document.createElement("button");
clear_all_logs_button.style.margin = "10px";
clear_all_logs_button.textContent = "Clear logs";
clear_all_logs_button.addEventListener("click", () => {
    send_request("GET", "clear_logs").then(r => {
        console.log(r.message);
        total_new_entries = 0;
    }).catch(e => {
        console.log("Could not clear log", e)
    })
});


let button_container = new Element({}, "");




let update_interval;
/******************************** IBC - UPDATE INTERVAL ****************************/
// each node has information on: process_name, instance_id and name/label

let update_interval_function = () => {
    if (Object.keys(instance_status).length > 0 && (Object.keys(instance_status).every(instance => instance_status[instance].status === "finished" || instance_status[instance].status === "stopped"))) {
        stop_updating();
        return;
    }
    send_request("POST", "digraph", {process_name: selection.process_name}).then(r => {
        update_last_updated_label();
        let dg = r.message;
        if(dg.length > 0) {
            update_graph_container(dg, selection.old_process === selection.process_name);
        } else {
            graph_container.text = "";
        } send_request("POST", "traces", {process_name: selection.process_name}).then(r => {
            traces_display_container.show();
            let traces = r.message;
            // Restart stopped instances
            restart_stopped_instances(traces);
            update_trace_information(traces);
        });
    });
}


let update_trace_information = traces => {
    if (traces.length > 0) {
        // console.log(traces)

        traces_display_container.apply_design({
            left: "",
            transform: "",
            width: ""
        });

        assign_links_and_colors_to_traces(traces);
        let width = traces_display_content.div.getBoundingClientRect().width;

        traces_display_container.apply_design({
            left: "50%",
            transform: "translate(-50%)",
            width: width+"px"
        });
    }
    else {
        traces_display_content.text = "No traces analyzed yet."
        let width = traces_display_content.div.getBoundingClientRect().width;
        traces_display_container.apply_design({
            left: "50%",
            transform: "translate(-50%)",
            width: width+"px"
        });
    }
    selection.old_process = selection.process_name;
}

let assign_links_and_colors_to_traces = traces => {
    traces_display_content.text = traces.replaceAll(/\n/g, "<br>").replaceAll(/;/g, "; ")
        .replaceAll(/(\d+): /g, (match, instance) => {
            let status = instance_status[instance] ? instance_status[instance].status : null;
            let color = status ? get_status_color(status) : "black";
            return `<a style='color: ${color}' href='https://cpee.org/flow/?monitor=https://cpee.org/flow/engine/${instance}/' target='_blank'>${instance}</a>: `;
        });
};

let get_status_color = status => {
    return status === "finished"? "green": status === "restarted"? "orange": status === "running"? "blue": status === "stopped"? "red": "black";
}


let restart_stopped_instances = traces => {
    const regex = /^\d+(?=:)/gm;
    let instances = traces.match(regex);
    if (instances === null) return;
    instances.map(s => parseInt(s)).forEach(instance => {
        // do not try to restart instances too often
        if (instance_status[instance] && instance_status[instance].n_restarted >= restart_threshold) {
            instance_status[instance].status = "stopped";
            return;
        }

        let url = `https://cpee.org/flow/engine/${instance}//properties/state/`;
        send_request("GET", url).then(r => {
            if (!instance_status[instance]) {
                instance_status[instance] = {n_restarted: 0, status: "running"};
            }
            if (r === "stopped") restart_instance(instance);
            if (r === "finished") instance_status[instance].status = "finished";
            if (r === "running") {
                if (instance_status[instance].status !== "restarted") {
                    instance_status[instance].status = "running";
                }
            }

            assign_links_and_colors_to_traces(traces);
        });
    });
};


let instance_status = {};  // instance: {n_restarted: int, status: str = finished|restarted|running|stopped},
let restart_threshold = 1;

let restart_instance = instance => {
    if (instance in instance_status) {
        instance_status[instance].n_restarted++;
        instance_status[instance].status = "restarted";
    } else {
        instance_status[instance] = {n_restarted: 1, status: "restarted"};
    }

    let url = `https://cpee.org/flow/engine/${instance}//properties/state/`;
    fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Origin': 'https://cpee.org',
            'Referer': `https://cpee.org/flow/?monitor=https://cpee.org/flow/engine/${instance}/`,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({value: "running"})
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        console.log(`Restarted instance ${instance} after it stopped.`);

    }).catch(_ => {
        console.log(`Could not restart instance ${instance}`);
    });
};



// Event-based updating
let total_new_entries = 0;
let batch_size = 10;
let event_source;

let start_event_listener = () => {
    event_source = new EventSource('/events');
    console.log("Started event listener")
    event_source.onerror = e => {
        // console.error('EventSource connection error:', e);
    };

    event_source.onmessage = event => {
        // console.log(`Received: ${event.data} new data entries`)
        let new_entries = event.data;
        total_new_entries += parseInt(new_entries);
        if (total_new_entries >= batch_size) {
            // console.log(`Updating model now after ${total_new_entries} new log entries`);
            update_interval_function();
            total_new_entries = 0;
        }
    };
}

// start_event_listener();

let stop_event_listener = () => {
    if (event_source) {
        event_source.close();
        event_source = null;
        total_new_entries = 0;
    }
}

/***************************************** GIBC ***********************************************/
graph_information_buttons_container.apply_design({
    width: "100vw",  // "calc(100vw - 40px)",
    display: "flex",
    justifyContent: "center",
    // margin: "20px",
    border: "0px solid red",
    position: "relative",
});

// Graph Container
let graph_container = new Element({
    width: "70vw",
    border: "3px solid black",
    display: "flex",
    justifyContent: "center",
    alignContent: "center",
    margin: "0",
    // height: "max(20em, 60vh)",
    height: "28em",
    overflow: "hidden", // SVG should not have width or height attributes,
    position: "relative",
}, `
<svg viewBox="72.00 72.00 657.00 116.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="border: 1px solid black;">
No SVG data yet.
</svg>
`)

let display_information = (aid, ainf, e, m, a, l) => {
    info_attributes.apply_design({width: "30%"})
    info_data.apply_design({width: "70%"})

    info_attr_id.text = "ID:";
    info_attr_name.text = "Name:";
    info_attr_earliest.text = "Earliest:";
    info_attr_median.text = "Median:";
    info_attr_average.text = "Average:";
    info_attr_latest.text = "Latest:";

    info_data_id.text = a + " ";
    info_data_name.text = ainf + " ";
    info_data_earliest.text = e + " ";
    info_data_median.text = m + " ";
    info_data_average.text = a + " ";
    info_data_latest.text = l + " ";
}


let display_no_information = () => {
    info_attributes.apply_design({width: "100%"})
    info_data.apply_design({width: "0%"})

    info_attr_id.text = "No information available."
    info_attr_name.text = " ";
    info_attr_earliest.text = " ";
    info_attr_median.text = " ";
    info_attr_average.text = " ";
    info_attr_latest.text = " ";

    info_data_id.text = " ";
    info_data_name.text = " ";
    info_data_earliest.text = " ";
    info_data_median.text = " ";
    info_data_average.text = " ";
    info_data_latest.text = " ";
};



let svg, digraph_options, mouse_drag, svg_data;



let init_graph_interactions = () => {

    digraph_options = {format: 'svg', engine: 'dot'};

    mouse_drag = {x: 0, y: 0};

    graph_container.div.addEventListener("mousedown", e1 => {
        if (e1.button === 2) {
            mouse_drag = {x: e1.x, y: e1.y, dx: 0, dy: 0};
            let translation = get_current_translations();
            svg_data.start_x = translation.x;
            svg_data.start_y = translation.y;
            graph_container.div.addEventListener("mousemove", svg_data.update_listener);
            graph_container.div.style.userSelect = "none";
            svg.userSelect = "none"
        } else if (e1.button === 0) {
            if (selection.svg_node && (e1.target === selection.svg_node.querySelector("polygon") || e1.target === selection.svg_node.querySelector("text"))) {
                console.log("clicked selected node")
                // && !(e1.target === selection.svg_node.querySelector("polygon") || e1.target === selection.svg_node.querySelector("text"))
            }
            if (selection.svg_node  && e1.target !== export_button) {  // deselect node
                // selection.svg_node.querySelector("polygon, ellipse").setAttribute("stroke", "black");
                selection.svg_node.querySelector("polygon, ellipse").setAttribute("fill", "rgba(0,0,0,0)")
                selection.deselected_node = selection.svg_node;
                selection.svg_node = null;
                selection.node_selector = null;
                graph_container.div.removeChild(card_container.div);
                display_no_information();
                // refresh_download_button();
            } else {

            }
            if (e1.target !== export_button) {
                refresh_download_button();
            }
        } else {
            console.log(e1.button)
        }

        // refresh_download_button();
    });

    graph_container.div.addEventListener("mouseup", e1 => {
        if (e1.button === 2) {
            graph_container.div.removeEventListener("mousemove", svg_data.update_listener);
            mouse_drag = {x: 0, y: 0, dx: 0, dy: 0};
            graph_container.div.style.userSelect = "";
            svg.userSelect = "";
            refresh_download_button();
        }
    });

    graph_container.div.addEventListener('wheel', (e) => {
        e.preventDefault();

        let svg_rect = svg.getBoundingClientRect();
        let mouse_x = e.clientX - svg_rect.left;
        let mouse_y = e.clientY - svg_rect.top;

        let vb = svg.getAttribute('viewBox').split(' ');
        let vbw = parseFloat(vb[2]);
        let vbh = parseFloat(vb[3]);
        let x_scale = vbw / svg_rect.width;
        let y_scale = vbh / svg_rect.height;
        let svg_x = mouse_x * x_scale + parseFloat(vb[0]);
        let svg_y = mouse_y * y_scale + parseFloat(vb[1]);

        let zoom = e.deltaY > 0 ? 1.1 : 0.9;
        let new_vbw = vbw * zoom;
        let new_vbh = vbh * zoom;

        let new_vbx = svg_x - (svg_x - parseFloat(vb[0])) * zoom;
        let new_vby = svg_y - (svg_y - parseFloat(vb[1])) * zoom;

        let newViewBoxAttr = `${isNaN(new_vbx)? 72: new_vbx} ${isNaN(new_vby)? 72: new_vby} ${new_vbw} ${new_vbh}`;
        svg.setAttribute('viewBox', newViewBoxAttr);

        refresh_download_button();
    });

    // prevent right click context menu
    graph_container.div.addEventListener("contextmenu", e => {
        e.preventDefault();
    });


    svg_data = {
        start_x: 0,
        start_y: 0,
        update_listener: e => {
            mouse_drag.dx = e.x - mouse_drag.x;
            mouse_drag.dy = e.y - mouse_drag.y;
            let vb = svg.getAttribute("viewBox").split(" ");
            svg_data.view_box = {x: parseFloat(vb[0]), y: parseFloat(vb[1]), w: parseFloat(vb[2]), h:parseFloat(vb[3])}
            let vbw = parseFloat(vb[2]),
                vbh = parseFloat(vb[3]);
            let display_width = parseFloat(window.getComputedStyle(graph_container.div).width.replace("px", "")),
                display_height = parseFloat(window.getComputedStyle(graph_container.div).height.replace("px", ""))

            let x_scale = svg_data.view_box.w / display_width,
                y_scale = svg_data.view_box.h / display_height;

            if (display_width/display_height < vbw/vbh) {
                y_scale = x_scale;
            } else if (display_width/display_height > vbw/vbh) {
                x_scale = y_scale;
            }

            set_translation({
                x: svg_data.start_x - mouse_drag.dx * x_scale,
                y: svg_data.start_y - mouse_drag.dy * y_scale,
            });
        },
        view_box: {x:0, y:0, w:0, h:0}
    }

    update_graph_interactions();
};

let update_graph_interactions = () => {
    // svg related
    svg = graph_container.div.querySelector("svg");
    if (window.getComputedStyle(graph_container.div).width.length !== 0) {
        svg.setAttribute("width", window.getComputedStyle(graph_container.div).width)
        svg.setAttribute("height", window.getComputedStyle(graph_container.div).height)
    }
    let vb = svg.getAttribute("viewBox").split(" ");
    svg_data.view_box = {x: parseFloat(vb[0]), y: parseFloat(vb[1]), w: parseFloat(vb[2]), h:parseFloat(vb[3])}
    svg.style.userSelect = "none";
    // svg.style.position = "static";
    // let places = document.querySelectorAll("g.place");

    let polygons = document.querySelectorAll("g.node > polygon, ellipse")
    polygons.forEach(p => {p.setAttribute("fill", "rgba(255,255,255,1)")})
    // console.log(polygons)
    // console.log(svg)
    // console.log(transitions)

    parse_activity_data()
    send_request("GET", "activity_data").then(activity_data => {
        parse_activity_data(activity_data);
        display_selected_node_information();
    }).catch(e => {});

    add_svg_interaction_listeners();
    if (selection.svg_node) process_selected_node();
}

let saved_activity_data = null;

let parse_activity_data = data => {
    if (data) saved_activity_data = data;
    else if (!saved_activity_data) return;
    let current_information = saved_activity_data[selection.process_name];

    let transitions = document.querySelectorAll("g.transition");
    transitions.forEach(t => {
        if (t.querySelector("text")) {
            let activity_id = t.querySelector("text").innerHTML;
            if (activity_id !== "τ" && current_information && current_information[activity_id]) t.querySelector("title").innerHTML = current_information[activity_id].name;
        }
    });
};


let add_node_interactions = e => {
    select_node(e);
};

let select_node = e => {
    let n = e.currentTarget;
    // console.log("Clicked: " + n.id);
    if (n === selection.deselected_node) {
        selection.deselected_node = null;
    } else {
        selection.svg_node = n;
        selection.node_selector = generate_node_selector(n);
        process_selected_node();
    }
}

let process_selected_node = () => {
    highlight_selected_node();
    display_selected_node_information();
    refresh_download_button();
};

let highlight_selected_node = () => {
    if (selection.node_selector) {
        let nodes = document.querySelectorAll('g.node');
        for(let node of nodes) {
            // console.log(e.innerHTML, selection.node_selector)
            if (generate_node_selector(node) === selection.node_selector) {
                selection.svg_node = node;
                let poly = selection.svg_node.querySelector("polygon, ellipse");
                // poly.setAttribute("stroke", "red");
                poly.setAttribute("fill", "rgba(255,0,0,0.5)")
                break;
            }
        }
    }
};

let display_selected_node_information = () => {
    // info_data_x (id, name, earliest, median, average, latest
    let current_information = saved_activity_data[selection.process_name];
    let node = selection.svg_node;
    if (node) {
        if (node.classList.contains("transition")) {
            let activity_id = node.querySelector("text").innerHTML;
            if (!activity_id.includes("τ")) {
                let activity_info = current_information[activity_id];
                // console.log(activity_info)
                let timestamps = Object.values(activity_info["timestamps"]).reduce((acc, timestamps) => acc.concat(timestamps), []);
                let dates = timestamps.map(timestamp => new Date(timestamp));
                dates.sort((a, b) => a - b);
                let format_date = date => {
                    let options = {
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    };
                    let formatted_date = date.toLocaleString('de-DE', options);
                    let time = formatted_date.split(',')[1];
                    let ddmmyyyy = formatted_date.split(',')[0];
                    return `${time}, ${ddmmyyyy}`;
                }
                let earliest = format_date(dates[0]);
                let median = format_date(dates[Math.floor(dates.length / 2)]);
                let latest = format_date(dates[dates.length - 1]);
                let sum = dates.reduce((acc, date) => acc + date.getTime(), 0);
                let average = format_date(new Date(sum / dates.length));

                display_information(activity_id,
                    activity_info.name ? activity_info.name : node.querySelector("text").innerHTML,
                    earliest, median, average, latest);
                // console.log()
            }
        } else {
            display_no_information();
        }

        graph_container.appendChild(card_container);
    }
};

let generate_node_selector = n => {
    let text = '';
    for (let i = 0; i < n.childNodes.length; i++) {
        const child = n.childNodes[i];
        if (child.tagName === "text") {
            text += child.innerHTML;
        }
    }
    return text;
    // return `${n.tagName}#${n.id}.${Array.from(n.classList).join(".")}`;
}




let update_graph_container = (digraph, same_process) => {
    // preserve viewbox, remove width and height attributes
    let old_svg = svg, old_viewbox;
    if (old_svg) old_viewbox = old_svg.getAttribute("viewBox");
    // digraph = digraph.replace(/tau/g, "τ")
    // graph_container.text = Viz(digraph, digraph_options);
    // console.log(digraph)
    new Viz().renderSVGElement(digraph).then(viz_svg => {
        graph_container.div.innerHTML = viz_svg.outerHTML;
        svg = graph_container.div.querySelector("svg");
        svg.style.border = "1px solid black";

        if (old_svg && same_process) {
            svg.setAttribute("viewBox", old_viewbox);
        }

        // init_graph_interactions();
        update_graph_interactions();
        add_svg_interaction_listeners();

        refresh_download_button();
        display_selected_node_information();
        graph_container.appendChild(last_updated_label);
    });
};

let add_svg_interaction_listeners = () => {
    let nodes = document.querySelectorAll("g.node");

    nodes.forEach(n => {
        n.removeEventListener("click", add_node_interactions);
        if (n.querySelector("text")) {  // tau-transitions are not clickable
            n.addEventListener("click", add_node_interactions);
        }
    });

    /* let edges = document.querySelectorAll("g.edge");
    /* let edges = document.querySelectorAll("g.edge");
    edges.forEach(n => {
        n.addEventListener("click", e => {console.log("Clicked: " + n.id)});
    }); */
};

let get_current_translations = () => {
    let vb = svg.getAttribute('viewBox').split(' ');
    let x = parseFloat(vb[0]);
    let y = parseFloat(vb[1]);
    return {x: x, y: y};
}

let set_translation = translation => {
    let vb = svg.getAttribute('viewBox').split(' ');
    svg.setAttribute('viewBox', `${translation.x} ${translation.y} ${parseFloat(vb[2])} ${parseFloat(vb[3])}`);
}


let last_updated_label = new Element({
    position: "absolute",
    left: "0",
    bottom: "0",
    margin: "5px",
}, "");

let update_last_updated_label = () => {
    last_updated_label.text = `Last updated: ${get_current_time()}`;
};

let get_current_time = () => {
    let now = new Date();

    let hours = String(now.getHours()).padStart(2, '0');
    let minutes = String(now.getMinutes()).padStart(2, '0');
    let seconds = String(now.getSeconds()).padStart(2, '0');
    let day = String(now.getDate()).padStart(2, '0');
    let month = String(now.getMonth() + 1).padStart(2, '0'); // January is 0
    let year = now.getFullYear();
    return `${hours}:${minutes}:${seconds}, ${day}.${month}.${year}`;
}

/***************************************** TD ***********************************************/
traces_display_container.apply_design({
    margin: "20px",
    maxHeight: "10em",
    // minWidth: "10vw",
    minHeight: "3em",
    border: "2px solid black",
    padding: "0.5em",
    // transform: "translate(-50%, 0)",
    // width: "70vw",
    position: "absolute",
    // left: "50%",
    overflowY: "hidden",
    display: "flex",
    justifyContent: "center",
    alignContent: "center",
    flexDirection: "column",
});

let traces_display_header = new Element({
    textAlign: "center", fontSize: "1.5em", fontWeight: "bold",
    margin: "0 auto",
}, "Traces");
let traces_display_content = new Element({
    overflow: "scroll",
    border: "0px solid orange",
    maxHeight: "calc(10em - 1.6em)",
    // width: "10vw",
    margin: "10px auto",
}, "No traces analyzed yet.");






/***************************************** GIBC - INFO CARD ***************************************/
let selection = {
    process_name: null,
    old_process: null,
    process_amount: null,
    svg_node: null,
    node_selector: null,
};


let card_container = new Element({  // selection root element
    borderRight: "3px solid black",
    borderBottom: "3px solid black",
    backgroundColor: "rgba(255,255,255,0.8)",
    width: "15em",
    position: "absolute",
    left: "0",
    top: "0",
    // height: "35em",
    overflowY: "scroll",
}, "");

/*
let selection_container = new Element({  // svg parent
    border: "0px solid red",
    width: "18em",
    margin: "1em"
}, "SVGs"); */

let info_container = new Element({  // info parent
    border: "0px solid red",
    display: "flex",
    margin: "0.75em",
}, "");

let info_attributes = new Element({
    width: "30%",
    userSelect: "none"
    // border: "0px solid lime"
}, "")

let info_data = new Element({
    width: "70%",
    // border: "0px solid yellow"
}, "")

let info_attr_id = new Element({}, "ID:");
let info_attr_name = new Element({}, "Name:");
let info_attr_earliest = new Element({}, "Earliest:");
let info_attr_median = new Element({}, "Median:");
let info_attr_average = new Element({}, "Average:");
let info_attr_latest = new Element({}, "Latest:");

let info_data_id = new Element({}, "2394879384");
let info_data_name = new Element({fontWeight: "bolder"}, "P3");
let info_data_earliest = new Element({}, "10:14");
let info_data_median = new Element({}, "10:23");
let info_data_average = new Element({}, "10:22");
let info_data_latest = new Element({}, "10:33");




let total_view_width_in_px, total_view_height_in_px;

window.onload = () => {
    total_view_width_in_px = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    total_view_height_in_px = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

    header_container.show();
    interaction_buttons_container.show();
    graph_information_buttons_container.show();
    // traces_display_container.show();

    // graph_information_buttons_container.appendChild(graph_container);

    interaction_buttons_container.appendChild(process_selector_container);
    process_selector_container.appendChild(process_selector_label, false);
    process_selector_container.appendChild(process_selector, false);
    process_selector_container.appendChild(process_amount_input, false);

    interaction_buttons_container.appendChild(update_mode_selector_container);
    update_mode_selector_container.appendChild(updated_mode_selector_label, false);
    update_mode_selector_container.appendChild(update_mode_selector, false);
    update_mode_selector_container.appendChild(update_mode_event_label, false);
    update_mode_selector_container.appendChild(update_mode_event_amount_input, false);


    interaction_buttons_container.appendChild(button_container);
    button_container.appendChild(process_submit_button, false);
    button_container.appendChild(stop_update_interval_button, false);
    button_container.appendChild(clear_all_logs_button, false);


    traces_display_container.appendChild(traces_display_header);
    traces_display_container.appendChild(traces_display_content);


    // card_container.appendChild(selection_container);
    card_container.appendChild(info_container)

    info_container.appendChild(info_attributes);
    info_container.appendChild(info_data);

    info_attributes.appendChild(info_attr_id);
    info_attributes.appendChild(info_attr_name);
    info_attributes.appendChild(info_attr_earliest);
    info_attributes.appendChild(info_attr_median);
    info_attributes.appendChild(info_attr_average);
    info_attributes.appendChild(info_attr_latest);

    info_data.appendChild(info_data_id);
    info_data.appendChild(info_data_name);
    info_data.appendChild(info_data_earliest);
    info_data.appendChild(info_data_median);
    info_data.appendChild(info_data_average);
    info_data.appendChild(info_data_latest);



    init_graph_interactions();
    display_no_information();

    card_container.div.addEventListener("contextmenu", e => {
        e.preventDefault();
    })

    let width = traces_display_content.div.getBoundingClientRect().width;
    traces_display_container.apply_design({
        left: "50%",
        transform: "translate(-50%)",
        width: width+"px"
    });
}