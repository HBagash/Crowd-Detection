import { IModelConnection, ScreenViewport } from "@itwin/core-frontend";
import { QueryRowFormat } from "@itwin/core-common";

export class Visualization {
  public static hideHouseExterior = async (vp: ScreenViewport, imodel: IModelConnection) => {
    const cToHide: string[] = [
      "'Geom_Baseline'",
      "'TC_Aggregate'",
      "'TC_Grass'",
      "'TC_Rail Ballast'",
      "'TC_Rail Conc Sleeper'",
      "'TC_Rail Subballast'",
      "'TL_Rail Subballast'",
      "'TL_Rail Ballast'",
      "'Default'",
      "'S-PILE-CONC'",
      "'S-WALL-CONC'",
      "'A-GLAZ'",
      "'A-GLAZ-CLER'",
      "'A-HRAL-MWRK'",
      "'ARC01'",
      "'S-BEAM'",
      "'S-BEAM-STEL-PRI'",
      "'S-COLS'",
      "'S-JOIS-ENVL'",
      "'S-SLAB-CONC'",
      "'C-RAIL-EQPM'",
      "'A-WALL-BLOC'",
      "'A-WALL-LINE'",
      "'A-WALL-METL'",
      "'A-WALL-STUD'",
      "'A-WALL-TPAR'",
      "'S-COLS-FRAM'",
      "'S-SLAB-CONC'",
      "'S-BEAM'",
      "'S-BEAM-CONC'",
      "'S-COLS-CONC'",
      "'A-CLNG-TILE'",
    ];

    const query = `SELECT ECInstanceId FROM Bis.Category WHERE CodeValue IN (${cToHide.toString()})`;

    const result = imodel.query(query, undefined, { rowFormat: QueryRowFormat.UseJsPropertyNames });
    const categoryIds: string[] = [];

    for await (const row of result) {
      categoryIds.push(row.id);
    }

    console.log(categoryIds);
    vp.changeCategoryDisplay(categoryIds, false);
  };
}
