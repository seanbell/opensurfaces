(function() {
  var ActionLog, UndoRedo, UndoableEvent;

  UndoableEvent = (function() {

    function UndoableEvent() {}

    UndoableEvent.prototype.undo = function(ui, state) {
      return console.log("error!");
    };

    UndoableEvent.prototype.run = function(ui, state) {
      return console.log("error!");
    };

    UndoableEvent.prototype.redo = function(ui, state) {
      return run();
    };

    UndoableEvent.prototype.entry = function() {
      throw {
        name: "TODO",
        message: "Unimplemetned Code"
      };
    };

    return UndoableEvent;

  })();

  UndoRedo = (function() {

    function UndoRedo(ui, args) {
      this.ui = ui;
      this.undo_btn = args.undo_btn;
      this.redo_btn = args.redo_btn;
      this.undo_stack = [];
      this.redo_stack = [];
      if (this.undo_btn != null) {
        $(this.undo_btn).on('click', function() {
          return this.undo();
        });
      }
      if (this.redo_btn != null) {
        $(this.redo_btn).on('click', function() {
          return this.redo();
        });
      }
      $(document).bind('keydown', 'ctrl_z meta_z', function() {
        return this.undo();
      });
      $(document).bind('keydown', 'ctrl_y meta_y', function() {
        return this.redo();
      });
    }

    UndoRedo.prototype.run = function(e) {
      e.run(this.ui, this.ui.state);
      this.undo_stack.push(e);
      this.redo_stack = [];
      this.ui.log.action(e.entry());
      return this.update_buttons();
    };

    UndoRedo.prototype.undo = function() {
      var e;
      if (this.can_undo) {
        e = this.undo_stack.pop();
        e.undo(this.ui, this.ui.state);
        this.redo_stack.push(e);
        this.ui.log.action({
          name: 'UndoRedo.undo'
        });
        return this.update_buttons();
      } else {
        return this.ui.log.attempted({
          name: 'UndoRedo.undo'
        });
      }
    };

    UndoRedo.prototype.redo = function() {
      var e;
      if (this.can_redo) {
        e = this.redo_stack.pop();
        e.redo(this.ui, this.ui.state);
        this.undo_stack.push(e);
        this.ui.log.action({
          name: 'UndoRedo.redo'
        });
        return this.update_buttons();
      } else {
        return this.ui.log.attempted({
          name: 'UndoRedo.redo'
        });
      }
    };

    UndoRedo.prototype.can_undo = function() {
      return this.undo_stack.length > 0;
    };

    UndoRedo.prototype.can_redo = function() {
      return this.redo_stack.length > 0;
    };

    UndoRedo.prototype.update_buttons = function() {
      if (this.undo_btn != null) {
        set_btn_enabled(this.undo_btn, this.can_undo());
      }
      if (this.redo_btn != null) {
        return set_btn_enabled(this.redo_btn, this.can_redo());
      }
    };

    return UndoRedo;

  })();

  ActionLog = (function() {

    function ActionLog() {
      this.entries = [];
    }

    ActionLog.prototype.action = function(args) {
      var _ref;
      if ((_ref = args.time) == null) {
        args.time = new Date();
      }
      args.done = true;
      return this.entries.push(args);
    };

    ActionLog.prototype.attempted = function(args) {
      var _ref;
      if ((_ref = args.time) == null) {
        args.time = new Date();
      }
      args.done = false;
      return this.entries.push(args);
    };

    return ActionLog;

  })();

}).call(this);
