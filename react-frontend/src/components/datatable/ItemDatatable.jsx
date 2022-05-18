import "./datatable.css"
import {DataGrid} from '@mui/x-data-grid';
import React, {useEffect, useState} from "react";
import LineChart from "../chart/LineChart";
import {object} from "prop-types";


function ItemDatatable({abtest_id, algorithm_id}) {

    const [loaded, setLoaded] = useState(false);
    const [select, setSelection] = React.useState([]);
    const [allRows, setAllRows] = useState(null);
    const [attributes, setAttributes] = useState(null)
    const [selectedAttributes, setSelectedAttributes] = useState(false)
    const [amountOfPurchases, setAmountOfPurchases] = useState(null)
    const [amountOfRecommendations, setAmountOfRecommendations] = useState(null)
    const [selectedGraphs, setSelectedGraphs] = useState(false)


    useEffect(() => {
        fetch('/api/items/' + abtest_id + "/" + algorithm_id, {
            method: 'GET',
            credentials: 'include',
            headers: {"Content-Type": "application/json", 'Accept': 'application/json'}
        }).then(res => res.json())
            .then((data) => {
                if (data.error) {
                    throw Error(data.error);
                }
                setLoaded(true)

                let row_list = []
                for (let i = 0; i < data.itemlist.length; i++) {
                    row_list.push({id: data.itemlist[i]})
                }

                setAllRows(row_list)

                // console.log(data.userlist)

            }).catch((err) => {
            console.log(err);
        })
    }, [abtest_id]);
    const columns = [
        {field: 'id', headerName: 'ID', width: 150}
    ];

    function showAttributeTab() {
        fetch('/api/items/metadata/' + abtest_id + '/' + select[0], {
            method: 'GET',
            credentials: 'include',
            headers: {"Content-Type": "application/json", 'Accept': 'application/json'}
        }).then(res => res.json())
            .then((data) => {
                if (data.error) {
                    throw Error(data.error);
                }
                setAttributes(data)
                setSelectedAttributes(true)
                setSelectedGraphs(false)
            }).catch((err) => {
            console.log(err);
        })
    }

    function showAttribute() {
        let string = ""
        for (let key in attributes) {
            string += key + ": "
            for (let value = 0; value < attributes[key].length; value++) {
                string += attributes[key][value]
                string += ", "
            }
            string += '\n'
        }
        return string
    }

    function showAmountOfPurchasesTab() {
        fetch('/api/items/purchases/' + abtest_id + '/' + select[0], {
            method: 'GET',
            credentials: 'include',
            headers: {"Content-Type": "application/json", 'Accept': 'application/json'}
        }).then(res => res.json())
            .then((data) => {
                if (data.error) {
                    throw Error(data.error);
                }
                let last_value = 0
                let day = 0
                let map = {graphdata: []}
                map["graphdata"].push(["Date", "AmountOfPurchases"])
                for (let key in data) {
                    day += 1
                    let new_value = data[key].length
                    new_value += last_value
                    data[key] = new_value / day
                    last_value = new_value
                    map["graphdata"].push([key, new_value])
                }

                setAmountOfPurchases(map)

            }).catch((err) => {
            console.log(err);
        })
    }

    function showAmountOfRecommendationsTab() {
        fetch('/api/items/recommendations/' + abtest_id + '/' + select[0], {
            method: 'GET',
            credentials: 'include',
            headers: {"Content-Type": "application/json", 'Accept': 'application/json'}
        }).then(res => res.json())
            .then((data) => {
                if (data.error) {
                    throw Error(data.error);
                }
                let last_value = 0
                let day = 0
                let map = {graphdata: []}
                map["graphdata"].push(["Date", "AmountOfPurchases"])
                for (let key in data) {
                    day += 1
                    let new_value = data[key].length
                    new_value += last_value
                    data[key] = new_value / day
                    last_value = new_value
                    map["graphdata"].push([key, new_value])
                }

                setAmountOfRecommendations(map)
                setSelectedGraphs(true)
                setSelectedAttributes(false)


            }).catch((err) => {
            console.log(err);
        })
    }

    function showAmountOfRecommendationsAndPurchasesTab() {
        fetch('/api/items/recommendations/purchases/' + abtest_id + '/' + select[0], {
            method: 'GET',
            credentials: 'include',
            headers: {"Content-Type": "application/json", 'Accept': 'application/json'}
        }).then(res => res.json())
            .then((data) => {
                if (data.error) {
                    throw Error(data.error);
                }
                let last_value = 0
                let day = 0
                let map = {graphdata: []}
                map["graphdata"].push(["Date", "AmountOfPurchases"])
                for (let key in data) {
                    day += 1
                    let new_value = data[key].length
                    new_value += last_value
                    data[key] = new_value / day
                    last_value = new_value
                    map["graphdata"].push([key, new_value])
                }

                setAmountOfRecommendations(map)
                setSelectedGraphs(true)
                setSelectedAttributes(false)


            }).catch((err) => {
            console.log(err);
        })
    }

    function fetchGraphs() {
        if (select[0]) {
            showAmountOfPurchasesTab()
            // showAmountOfRecommendationsAndPurchasesTab()
            showAmountOfRecommendationsTab()

        }
    }

    return (
        <div className="page">
            <label>All active Items</label>
            <div className="row text-left align-content-left justify-content-left">
                <div className="datatable" style={{height: 400, width: '50%'}}>
                    <div className="datatableTitle">
                        <DataGrid style={{height: 400, width: '50%'}} className="col-12 col-lg-6 col-xl-6 col-xxl-6 "
                                  rows={allRows}
                            // columns={columns.concat(actionColumn)}
                                  columns={columns}
                                  pageSize={5}
                                  checkboxSelection
                                  onSelectionModelChange={(newSelection) => {
                                      setSelection(newSelection);
                                  }}
                        />
                    </div>
                </div>

            </div>
            <button className="position-relative " onClick={showAttributeTab}>Metadata</button>
            <button className="position-relative " onClick={fetchGraphs}>Purchases</button>
            {selectedAttributes && !selectedGraphs &&
                <br></br> &&
                <div className="col-12 col-lg-6 col-xl-6 col-xxl-6 ">
                    <label>Attributes </label>
                    <div style={{flex: 1, padding: 20, backgroundColor: "grey", height: 400, width: '200%'}}>
                        {showAttribute()}
                    </div>
                </div>}
            {selectedGraphs && <br></br> && !selectedAttributes &&
                <div>
                    <div className="row text-center align-content-center justify-content-center">
                        <div className="col-12 col-lg-6 col-xl-6 col-xxl-6" style={{height: "400px"}}>
                            <LineChart chart_id={1} title="Amount Of Purchases" xMin={0}
                                       xMax={amountOfPurchases.size}
                                       XFnY={amountOfPurchases}/>
                        </div>
                        <div className="col-12 col-lg-6 col-xl-6 col-xxl-6" style={{height: "400px"}}>
                            <LineChart chart_id={2} title={"Recommendations"} xMin={0}
                                       xMax={amountOfRecommendations.size} XFnY={amountOfRecommendations}/>
                        </div>
                    </div>
                    <div className="row text-center align-content-center justify-content-center">
                        {/*<div className="col-12 col-lg-6 col-xl-6 col-xxl-6" style={{height: "400px"}}>*/}
                        {/*    <LineChart chart_id={1} title="Amount Of Purchases" xMin={0}*/}
                        {/*               xMax={amountOfPurchases.size}*/}
                        {/*               XFnY={amountOfPurchases}/>*/}
                        {/*</div>*/}
                    </div>
                </div>
            }
        </div>
    );
}

export default ItemDatatable;