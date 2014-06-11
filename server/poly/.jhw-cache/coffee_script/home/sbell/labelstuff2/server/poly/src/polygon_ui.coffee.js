(function() {
  var ControllerState, ControllerUI, PolygonUI, StageUI, UEClosePolygon, UECreatePolygon, UEDragVertex, UEPushPoint, UEToggleMode,
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  ControllerUI = (function() {

    function ControllerUI(args) {
      var _this = this;
      this.state = new ControllerState(args);
      this.undoredo = new UndoRedo(this, args);
      this.log = new ActionLog();
      this.btn_draw = args.btn_draw;
      this.btn_edit = args.btn_edit;
      $(this.btn_draw).on('click', function() {
        if (!_this.state.draw_mode) {
          return _this.ui_toggle_mode();
        }
      });
      $(this.btn_edit).on('click', function() {
        if (_this.state.draw_mode) {
          return _this.ui_toggle_mode();
        }
      });
      set_btn_enabled(this.btn_draw, false);
      set_btn_enabled(this.btn_edit, false);
      $(document).on('contextmenu', function() {
        return false;
      });
    }

    ControllerUI.prototype.click = function(e) {
      var ue;
      if (this.draw_mode) {
        if (e.button > 1) {
          ue = new UEClosePolygon();
          if ((this.open_poly != null) && this.open_poly.can_close()) {
            return this.undoredo.run(this, ue);
          } else {
            return this.log.attempted(ue.entry());
          }
        } else {
          return this.undoredo.run(this, (function() {
            if (this.open_poly != null) {
              ue = new UEPushPoint(this.stage.mouse_pos());
              if (this.open_poly.can_push_point(p)) {
                return this.undoredo.run(this, ue);
              } else {
                return this.log.attempted(ue.entry());
              }
            } else {
              return new UECreatePolygon(this.stage.mouse_pos());
            }
          })());
        }
      }
    };

    ControllerUI.prototype.select_poly = function(id) {
      if (this.state.sel_poly != null) {
        if (id === this.state.sel_poly.id) {
          return;
        }
        this.sel_poly.remove_anchors();
      }
      this.state.sel_poly = this.state.get_poly(id);
      return this.state.sel_poly.add_anchors();
    };

    ControllerUI.prototype.start_drag_point = function(id, i) {
      return this.state.save_point(id, i);
    };

    ControllerUI.prototype.revert_drag_point = function(id, i) {
      var p;
      p = this.state.unsave_point(id, i);
      return this.state.sel_poly.poly.set_point(i, p);
    };

    ControllerUI.prototype.progress_drag_point = function(id, i, p) {
      return this.state.sel_poly.poly.set_point(i, p);
    };

    ControllerUI.prototype.finish_drag_point = function(id, i, p) {
      this.state.unsave_point(id, i);
      return this.undoredo.run(this.state, new UEDragVertex(id, i, p));
    };

    ControllerUI.prototype.drag_valid = function(id, i) {
      return !this.state.sel_poly.self_intersects_at_index(i);
    };

    ControllerUI.prototype.toggle_mode = function() {
      return this.undoredo.run(this.state, new UEToggleMode());
    };

    ControllerUI.prototype.update_buttons = function() {
      set_btn_enabled(this.btn_draw, this.state.draw_mode());
      return set_btn_enabled(this.btn_edit, !this.state.draw_mode);
    };

    ControllerUI.prototype.photo_loaded = function() {
      this.update_buttons();
      return this.state.stage_ui.init_events();
    };

    ControllerUI.prototype.get_submit_data = function() {
      return {
        polys: this.state.get_all_poly_points,
        log: this.log,
        version: 1
      };
    };

    return ControllerUI;

  })();

  ControllerState = (function() {

    function ControllerState(args) {
      this.stage_ui = new StageUI(args);
      this.closed_polys = [];
      this.open_poly = null;
      this.draw_mode = true;
      this.sel_poly = null;
      this.saved_point = null;
    }

    ControllerState.prototype.push_point = function(p) {
      var _ref;
      if ((_ref = this.open_poly) != null) {
        _ref.poly.push_point(p);
      }
      return this.open_poly;
    };

    ControllerState.prototype.pop_point = function() {
      var _ref;
      if ((_ref = this.open_poly) != null) {
        _ref.poly.pop_point();
      }
      return this.open_poly;
    };

    ControllerState.prototype.set_point = function(id, i, p) {
      var poly;
      poly = this.get_poly(id);
      poly.poly.set_point(i, p);
      return poly;
    };

    ControllerState.prototype.get_point = function(id, i) {
      var _ref;
      return (_ref = this.get_poly(id)) != null ? _ref.poly.get_point(i) : void 0;
    };

    ControllerState.prototype.create_poly = function(p) {
      if (this.open_poly != null) {
        this.open_poly.remove_all();
      }
      return this.open_poly = new PolygonUI(new Polygon(p), this.stage_ui);
    };

    ControllerState.prototype.get_poly = function(id) {
      return this.closed_polys[id];
    };

    ControllerState.prototype.remove_poly = function() {
      var _ref;
      if ((_ref = this.open_poly) != null) {
        _ref.remove_all();
      }
      return this.open_poly = null;
    };

    ControllerState.prototype.close_poly = function() {
      var poly;
      if (this.open_poly != null) {
        poly = this.open_poly;
        this.open_poly.poly.close();
        this.closed_polys.push(this.open_poly);
        this.open_poly = null;
        return poly;
      } else {
        return null;
      }
    };

    ControllerState.prototype.unclose_poly = function() {
      if (this.closed_polys.length > 0) {
        this.open_poly = this.closed_polys.pop();
        this.open_poly.poly.unclose();
        return this.open_poly;
      } else {
        return null;
      }
    };

    ControllerState.prototype.save_point = function(i) {
      if (!(this.saved_point != null)) {
        return this.saved_point = clone_pt(this.sel_poly.get_point(i));
      }
    };

    ControllerState.prototype.unsave_point = function() {
      var ret;
      ret = this.saved_point;
      this.saved_point = null;
      return ret;
    };

    ControllerState.prototype.toggle_mode = function() {
      this.draw_mode = !draw_mode;
      if (draw_mode) {
        if (this.sel_poly != null) {
          this.sel_poly.remove_anchors();
          return this.sel_poly = null;
        }
      } else {
        if (this.open_poly != null) {
          this.open_poly.remove_all();
          return this.open_poly = null;
        }
      }
    };

    ControllerState.prototype.get_all_poly_points = function() {
      var p;
      return [
        (function() {
          var _i, _len, _ref, _results;
          _ref = this.closed_polys;
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            p = _ref[_i];
            _results.push(p.poly.points);
          }
          return _results;
        }).call(this)
      ];
    };

    return ControllerState;

  })();

  UEToggleMode = (function(_super) {

    __extends(UEToggleMode, _super);

    function UEToggleMode() {
      this.open_points = null;
      this.sel_poly_id = null;
    }

    UEToggleMode.prototype.run = function(ui, state) {
      var _ref, _ref1;
      if (state.draw_mode) {
        this.open_points = (_ref = state.open_poly) != null ? _ref.clone_points() : void 0;
      } else {
        this.sel_poly_id = (_ref1 = state.sel_poly) != null ? _ref1.id : void 0;
      }
      state.toggle_mode();
      return ui.update_buttons();
    };

    UEToggleMode.prototype.redo = function(ui, state) {
      state.toggle_mode();
      return ui.update_buttons();
    };

    UEToggleMode.prototype.undo = function(ui, state) {
      var _ref, _ref1;
      state.toggle_mode();
      if (state.draw_mode) {
        if (this.open_points != null) {
          return (_ref = state.create_poly(this.open_points)) != null ? _ref.update(ui) : void 0;
        }
      } else {
        if (this.sel_poly_id != null) {
          return (_ref1 = state.select_poly(this.sel_poly_id)) != null ? _ref1.update(ui) : void 0;
        }
      }
    };

    UEToggleMode.prototype.entry = function() {
      return {
        name: "UEToggleMode"
      };
    };

    return UEToggleMode;

  })(UndoableEvent);

  UEPushPoint = (function(_super) {

    __extends(UEPushPoint, _super);

    function UEPushPoint(p) {
      this.p = clone_pt(p);
    }

    UEPushPoint.prototype.run = function(ui, state) {
      var _ref;
      return (_ref = state.push_point(this.p)) != null ? _ref.update(ui) : void 0;
    };

    UEPushPoint.prototype.undo = function(ui, state) {
      var _ref;
      return (_ref = state.pop_point()) != null ? _ref.update(ui) : void 0;
    };

    UEPushPoint.prototype.entry = function() {
      return {
        name: "UEPushPoint",
        args: {
          p: this.p
        }
      };
    };

    return UEPushPoint;

  })(UndoableEvent);

  UECreatePolygon = (function(_super) {

    __extends(UECreatePolygon, _super);

    function UECreatePolygon(p) {
      this.p = clone_pt(p);
    }

    UECreatePolygon.prototype.run = function(ui, state) {
      var _ref;
      return (_ref = state.create_poly([this.p])) != null ? _ref.update(ui) : void 0;
    };

    UECreatePolygon.prototype.undo = function(ui, state) {
      var _ref;
      return (_ref = state.remove_poly()) != null ? _ref.update(ui) : void 0;
    };

    UECreatePolygon.prototype.entry = function() {
      return {
        name: "UECreatePolygon",
        args: {
          p: this.p
        }
      };
    };

    return UECreatePolygon;

  })(UndoableEvent);

  UEClosePolygon = (function(_super) {

    __extends(UEClosePolygon, _super);

    function UEClosePolygon() {
      return UEClosePolygon.__super__.constructor.apply(this, arguments);
    }

    UEClosePolygon.prototype.run = function(ui, state) {
      var _ref;
      return (_ref = state.close_poly()) != null ? _ref.update(ui) : void 0;
    };

    UEClosePolygon.prototype.undo = function(ui, state) {
      var _ref;
      return (_ref = state.unclose_poly()) != null ? _ref.update(ui) : void 0;
    };

    UEClosePolygon.prototype.entry = function() {
      return {
        name: "UEClosePolygon"
      };
    };

    return UEClosePolygon;

  })(UndoableEvent);

  UEDragVertex = (function(_super) {

    __extends(UEDragVertex, _super);

    function UEDragVertex(id, i, p) {
      this.id = id;
      this.i = i;
      this.p1 = clone_pt(p);
    }

    UEDragVertex.prototype.run = function(ui, state) {
      var _ref;
      this.p0 = state.get_point(this.id, this.i);
      return (_ref = state.set_point(this.id, this.i, this.p1)) != null ? _ref.update(ui) : void 0;
    };

    UEDragVertex.prototype.redo = function(ui, state) {
      var _ref;
      return (_ref = state.set_point(this.id, this.i, this.p1)) != null ? _ref.update(ui) : void 0;
    };

    UEDragVertex.prototype.undo = function(ui, state) {
      var _ref;
      return (_ref = state.set_point(this.id, this.i, this.p0)) != null ? _ref.update(ui) : void 0;
    };

    UEDragVertex.prototype.entry = function() {
      return {
        name: "UEDragVertex",
        args: {
          id: this.id,
          i: this.i,
          p: this.p1
        }
      };
    };

    return UEDragVertex;

  })(UndoableEvent);

  StageUI = (function() {

    function StageUI(args) {
      this.width = args.width;
      this.height = args.height;
      this.stage = new Kinetic.Stage({
        container: args.container,
        width: this.width,
        height: this.height
      });
      this.layer = new Kinetic.Layer();
      this.stage.add(this.layer);
      this.loading = new Kinetic.Text({
        x: 30,
        y: 30,
        text: "Loading...",
        align: "left",
        fontSize: 32,
        fontFamily: "Verdana",
        textFill: "#000"
      });
      this.layer.add(this.loading);
      this.layer.draw();
    }

    StageUI.prototype.init_events = function(ui) {
      this.stage.on('mouseout', function() {
        return this.layer.draw();
      });
      this.stage.on('mousemove', ui.update);
      return this.stage.on('mousedown', ui.click);
    };

    StageUI.prototype.add = function(o, opacity) {
      this.layer.add(o);
      o.setOpacity(0);
      return o.transitionTo({
        opacity: opacity,
        duration: 0.4
      });
    };

    StageUI.prototype.remove = function(o) {
      if (o != null) {
        if (o.add_trans != null) {
          o.add_trans.stop();
        }
        return o.transitionTo({
          opacity: 0,
          duration: 0.4
        }, {
          callback: (function(o) {
            return function() {
              return o.remove();
            };
          })(o)
        });
      }
    };

    StageUI.prototype.mouse_pos = function() {
      return this.stage.getMousePosition();
    };

    StageUI.prototype.set_photo = function(photo_obj, ui) {
      return photo_obj.onload = (function(photo_obj) {
        return function() {
          this.layer.remove(this.loading);
          this.loading = null;
          this.photo = new Kinetic.Image({
            x: 0,
            y: 0,
            this.image: photo_obj,
            width: this.width,
            height: this.height
          });
          this.layer.add(this.photo);
          this.photo.moveToBottom();
          return ui.photo_loaded();
        };
      })(photo_obj);
    };

    return StageUI;

  })();

  PolygonUI = (function() {

    function PolygonUI(poly, stage) {
      this.poly = poly;
      this.stage = stage;
      this.line = null;
      this.fill = null;
      this.text = null;
      this.hover_line = null;
      this.hover_fill = null;
      this.anchors = null;
    }

    PolygonUI.prototype.update = function(ui) {
      var p;
      if (this.poly.open) {
        this.remove_fill();
        this.remove_text();
        this.add_line();
        p = this.stage.mouse_pos();
        if ((p != null) && !this.poly.empy()) {
          this.add_hover(p);
        } else {
          this.remove_hover();
        }
      } else {
        this.remove_hover();
        this.remove_line();
        this.add_fill(ui);
        this.add_text();
      }
      return this.stage.draw();
    };

    PolygonUI.prototype.remove_line = function() {
      this.stage.remove(this.line);
      return this.line = null;
    };

    PolygonUI.prototype.remove_fill = function() {
      this.stage.remove(this.fill);
      return this.fill = null;
    };

    PolygonUI.prototype.remove_text = function() {
      this.stage.remove(this.text);
      return this.text = null;
    };

    PolygonUI.prototype.remove_hover = function() {
      this.stage.remove(this.hover_fill);
      this.hover_fill = null;
      this.stage.remove(this.hover_line);
      return this.hover_line = null;
    };

    PolygonUI.prototype.remove_anchors = function() {
      var a, _i, _len, _ref;
      _ref = this.anchors;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        a = _ref[_i];
        this.stage.remove(a);
      }
      return this.anchors = null;
    };

    PolygonUI.prototype.remove_all = function() {
      this.remove_line();
      this.remove_fill();
      this.remove_text();
      this.remove_hover();
      return this.remove_anchors();
    };

    PolygonUI.prototype.add_fill = function(ui) {
      var COLORS,
        _this = this;
      if (this.fill != null) {
        return this.fill.setPoints(this.poly.points);
      } else {
        COLORS = ['#5D8AA8', '#3B7A57', '#915C83', '#A52A2A', '#FFE135', '#2E5894', '#3D2B1F', '#FE6F5E', '#ACE5EE', '#006A4E', '#873260', '#CD7F32', '#BD33A4', '#1E4D2B', '#DE6FA1', '#965A3E', '#002E63', '#FF3800', '#007BBB', '#6F4E37', '#0F4D92', '#9F1D35', '#B78727', '#8878C3', '#30D5C8', '#417DC1', '#FF6347'];
        this.fill = new Kinetc.Polygon({
          points: this.poly.points,
          fill: COLORS[this.id % COLORS.length],
          stroke: '#007',
          wrokeWidth: 2,
          lineJoin: 'round'
        });
        this.fill.on('click', function() {
          return ui.select_poly(_this.id);
        });
        return this.stage.add(this.fill, 0.5);
      }
    };

    PolygonUI.prototype.add_text = function() {
      var cen, label, pos;
      cen = this.poly.centroid();
      label = String(this.id + 1);
      pos = {
        x: cen.x - 5 * label.length,
        y: cen.y - 5
      };
      if (this.text != null) {
        return this.text.setPosition(pos);
      } else {
        this.text = new Kinetic.Text({
          text: label,
          textFill: '#000',
          x: pos.x,
          y: pos.y,
          align: 'left',
          fontSize: 10,
          fontFamily: 'Verdana',
          fontStyle: 'bold'
        });
        return this.stage.add(this.text, 1.0);
      }
    };

    PolygonUI.prototype.add_line = function() {
      if (this.line != null) {
        return this.line.setPoints(this.poly.points);
      } else {
        this.line = new Kinetic.Line({
          points: this.points,
          opacity: 0,
          stroke: "#00F",
          strokeWidth: 4,
          lineJoin: "round"
        });
        return this.stage.add(this.line, 0.5);
      }
    };

    PolygonUI.prototype.add_hover = function(p) {
      add_hover_poly(p);
      return add_hover_line(p);
    };

    PolygonUI.prototype.add_hover_poly = function(p) {
      var hover_points;
      hover_points = this.poly.points.concat([clone_pt(p)]);
      if (this.hover_poly != null) {
        return this.hover_poly.setPoints(hover_points);
      } else {
        this.hover_poly = new Kinetic.Polygon({
          points: hover_points,
          opacity: 0,
          fill: "#00F"
        });
        return this.stage.add(this.hover_poly, 0.15);
      }
    };

    PolygonUI.prototype.add_hover_line = function(p) {
      var hover_points;
      hover_points = [clone_pt(p, this.poly.points[this.poly.num_points()])];
      if (this.hover_line) {
        return this.hover_line.setPoints(hover_points);
      } else {
        this.hover_line = new Kinetic.Line({
          points: hover_line_points,
          opacity: 0,
          stroke: "#FFF",
          strokeWidth: 4,
          lineJoine: "round"
        });
        return this.stage.add(this.hover_line, 0.5);
      }
    };

    PolygonUI.prototype.add_anchors = function(ui) {
      var i, v, _i, _ref,
        _this = this;
      if (!(this.anchors != null)) {
        return;
      }
      this.anchors = [];
      for (i = _i = 0, _ref = this.points.num_points(); 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        v = new Kinetic.Circle({
          x: this.points[i].x,
          y: this.points[i].y,
          radius: 8,
          strokeWidth: 2,
          stroke: "#666",
          fill: "#ddd",
          opacity: 0,
          draggable: true
        });
        this.anchors.push(v);
        v.on('mouseover', (function(i) {
          return function() {
            _this.anchors[i].setStrokeWidth(4);
            return _this.stage.draw();
          };
        })(i));
        v.on('mouseout', (function(i) {
          return function() {
            _this.anchors[i].setStrokeWidth(2);
            return _this.stage.draw();
          };
        })(i));
        v.on('mousedown', (function(i) {
          return function() {
            return ui.start_drag_point(_this.id, i);
          };
        })(i));
        v.on('dragmove', (function(i) {
          return function() {
            ui.progress_drag_point(_this.id, i, _this.anchors[i].getPosition());
            if (_this.fill) {
              if (ui.drag_valid(_this.id, i)) {
                _this.fill.setStrokeWidth(10);
                return _this.fill.setStroke("#F00");
              } else {
                _this.fill.setStrokeWidth(2);
                return _this.fill.setStroke("#007");
              }
            }
          };
        })(i));
        v.on('dragend', (function(i) {
          return function() {
            if (ui.drag_valid(_this.id, i)) {
              ui.revert_drag_point(_this.id, i);
            } else {
              ui.finish_drag_point(_this.id, i, _this.anchors[i].getPosition());
            }
            _this.fill.setStrokeWidth(2);
            _this.fill.setStroke("#007");
            return _this.stage.draw();
          };
        })(i));
        this.stage.add(v);
      }
      return this.stage.draw();
    };

    return PolygonUI;

  })();

  namespace("Polys", function(exports) {
    return exports.ControllerUI = ControllerUI;
  });

}).call(this);
