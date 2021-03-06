/**
 * Copyright (c) 2005-2011 by Appcelerator, Inc. All Rights Reserved.
 * Licensed under the terms of the Eclipse Public License (EPL).
 * Please see the license.txt included with this distribution for details.
 * Any modifications to this file must keep this entire header intact.
 */
package org.python.pydev.core.parser;

import org.eclipse.core.runtime.IAdaptable;
import org.eclipse.jface.text.IDocument;

public interface IParserObserver2 {

    /**
     * Has the argsToReparse additional Parameter
     */
    void parserChanged(ISimpleNode root, IAdaptable file, IDocument doc, Object... argsToReparse);

    /**
     * Has the argsToReparse additional Parameter
     */
    void parserError(Throwable error, IAdaptable file, IDocument doc, Object... argsToReparse);

}
