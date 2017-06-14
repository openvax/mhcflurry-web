import 'stylesheets/base'
import 'stylesheets/config/colors'


import React from 'react'
import ReactDOM from 'react-dom'
import Container from 'javascripts/container'

//ReactDOM.render(<Container />, document.querySelector('#main'))


import Select from 'react-select';

var options = [
  { value: 'one', label: 'One' },
  { value: 'two', label: 'Two' }
];

function logChange(val) {
  console.log("Selected: " + val);
}

const showSelectBox = (element) => {
  ReactDOM.render(<Select name="form-field-name" value="one" options={options} onChange={logChange} />, element);
};


const ReactDataGrid = require('react-data-grid');

const Example = React.createClass({
  getInitialState() {
    this.createRows();
    this._columns = [
      {
        key: 'id',
        name: 'ID',
        locked: true
      },
      {
        key: 'task',
        name: 'Title',
        width: 200
      },
      {
        key: 'priority',
        name: 'Priority',
        width: 200
      },
      {
        key: 'issueType',
        name: 'Issue Type',
        width: 200
      },
      {
        key: 'complete',
        name: '% Complete',
        width: 200
      },
      {
        key: 'startDate',
        name: 'Start Date',
        width: 200
      },
      {
        key: 'completeDate',
        name: 'Expected Complete',
        width: 200
      }
    ];

    return null;
  },

  getRandomDate(start, end) {
    return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime())).toLocaleDateString();
  },

  createRows() {
    let rows = [];
    for (let i = 1; i < 1000; i++) {
      rows.push({
        id: i,
        task: 'Task ' + i,
        complete: Math.min(100, Math.round(Math.random() * 110)),
        priority: ['Critical', 'High', 'Medium', 'Low'][Math.floor((Math.random() * 3) + 1)],
        issueType: ['Bug', 'Improvement', 'Epic', 'Story'][Math.floor((Math.random() * 3) + 1)],
        startDate: this.getRandomDate(new Date(2015, 3, 1), new Date()),
        completeDate: this.getRandomDate(new Date(), new Date(2016, 0, 1))
      });
    }

    this._rows = rows;
  },

  rowGetter(i) {
    return this._rows[i];
  },

  render() {
    return  (
      <ReactDataGrid
        columns={this._columns}
        rowGetter={this.rowGetter}
        rowsCount={this._rows.length}
        minHeight={500}
        enableCellSelect={true}
        cellNavigationMode="changeRow" />);
  }
});

const showExampleGrid = (element) => {
  ReactDOM.render(<Example />, element);
};


module.exports = {
"showSelectBox2": showSelectBox,
"exampleWrapper": showExampleGrid
};

