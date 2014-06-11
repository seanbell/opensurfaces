describe 'UndoableEvent', ->

  beforeEach, -> @ue = new UndoableEvent()

  it "throws an exception", ->
    expect(@ue.undo()).toThrow();
    expect(@ue.redo()).toThrow();
    expect(@ue.run()).toThrow();
    expect(@ue.entry()).toThrow();

describe 'UndoRedo', ->

  beforeEach, ->
    @ur = new UndoRedo()

