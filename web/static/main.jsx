var nbsp = '\u00a0';

function getSocketIOUrl() {
  var urlBase =
    location.protocol + '//' +
    location.hostname +
    (location.port ? ':'+location.port: '');
  return urlBase + '/client';
}

function ServerConnection(url, onUpdateState) {
  this.socket = io.connect(url);
  this.socket.on('update', onUpdateState);
}
ServerConnection.prototype.getSocket = function() { return this.socket; };
ServerConnection.prototype.addBreakpoint = function(addr) {
  this.socket.emit('rpc', {method: 'set_breakpoint', args: {
    address: addr
  }});
};
ServerConnection.prototype.deleteBreakpoint = function(addr) {
  this.socket.emit('rpc', {method: 'delete_breakpoint', args: {
    address: addr
  }});
};

var GdbWeb = React.createClass({
  getInitialState: function() {
    return null;
  },
  componentDidMount: function() {
    this.api = new ServerConnection(getSocketIOUrl(), this.setState.bind(this));
  },
  loading: function() {
    return (<p>Loading...</p>);
  },
  render: function() {
    if (this.state === null)
      return this.loading();

    var dataViews = this.state.dataViews.map(function(view) {
      return (
        <td className='cell-memory'>
          <DataView api={this.api} info={this.state.info} view={view} />
        </td>);
    }.bind(this));

    return (
      <div>
        <table className='table-top'>
          <tr>
            <td className='cell-assembly'>
              <AssemblyView api={this.api} info={this.state.info} view={this.state.assemblyView} />
            </td>
            <td className='cell-registers'>
              <Registers api={this.api} info={this.state.info} />
            </td>
          </tr>
        </table>
        <table className='table-bottom'>
          <tr>
            {dataViews}
          </tr>
        </table>
      </div>);
  },
});

var DataView = React.createClass({
  render: function() {
    var rows = this.props.view.result.map(function(word) {
      return (
        <tr>
          <td className='col-address'>0x{word.address.hexPadded}</td>
          <td className='col-value'>0x{word.value.hexPadded}</td>
        </tr>);
    });
    return (
      <table className='memory'>
        {rows}
      </table>);
  }
});

var Registers = React.createClass({
  render: function() {
    var regRows = this.props.info.registers.map(function(reg) {
      return (
        <tr>
          <td className='col-name'>
            {reg.name}
          </td>
          <td className='col-value-hex'>
            0x{reg.value.hexPadded}
          </td>
          <td className='col-value-smart'>
            {reg.value.smart ? reg.value.smart : ''}
          </td>
        </tr>);
    }.bind(this));
    return (
      <table className='registers'>
        {regRows}
      </table>);
  },
});

var getHex = function(num) {
  return num.hex;
};

var AssemblyView = React.createClass({
  render: function() {
    var insRows = this.props.view.result.map(function(ins) {
      var isBreakpoint =
          this.props.info.breakpoints.map(getHex).indexOf(ins.address.hex) >= 0;
      var isActive = ins.address.hex === this.props.info.ip.hex;
      var toggleBreakpoint = function() {
        (isBreakpoint
            ? this.props.api.deleteBreakpoint
            : this.props.api.addBreakpoint).bind(this.props.api)(ins.address.hex);
      }.bind(this);

      return (
        <tr className={isActive ? 'active' : ''}>
          <td className='col-marker' onClick={toggleBreakpoint}>
            <div className={'breakpoint-marker ' + (isBreakpoint ? 'active' : '')}>
            </div>
          </td>
          <td className='col-address'>
            0x{ins.address.hexPadded}
          </td>
          <td className='col-label'>
            {ins.label}
          </td>
          <td className='col-mnemonic'>
            {ins.mnemonic}
          </td>
          <td className='col-op'>
            {ins.op_str}
          </td>
        </tr>);
    }.bind(this));
    return (
      <table className='assembly'>
        {insRows}
      </table>);
  }
});

React.render(
  React.createElement(GdbWeb, null),
  document.getElementById('content')
);
