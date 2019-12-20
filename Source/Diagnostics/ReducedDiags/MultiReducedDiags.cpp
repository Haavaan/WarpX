#include "MultiReducedDiags.H"
#include "AMReX_ParmParse.H"
#include "AMReX_ParallelDescriptor.H"
#include <fstream>

/// constructor
MultiReducedDiags::MultiReducedDiags ()
{

    /// read reduced diags names
    amrex::ParmParse pp("warpx");
    m_plot_rd = pp.queryarr("reduced_diags_names", m_rd_names);

    /// if names are not given, reduced diags will not be done
    if ( m_plot_rd == 0 ) { return; }

    /// resize
    m_multi_rd.resize(m_rd_names.size());

    /// loop over all reduced diags
    for (int i_rd = 0; i_rd < m_rd_names.size(); ++i_rd)
    {

        amrex::ParmParse pp(m_rd_names[i_rd]);

        /// read reduced diags type
        std::string rd_type;
        pp.query("type", rd_type);

        /// match diags
        if (rd_type.compare("ParticleMeanEnergy") == 0)
        {
            m_multi_rd[i_rd].reset
                ( new ParticleMeanEnergy(m_rd_names[i_rd]));
        }
        else if (rd_type.compare("FieldMeanEnergy") == 0)
        {

        }
        else
        { amrex::Abort("No matching reduced diagnostics type found."); }
        ///< end if match diags

    }
    ///< end loop over all reduced diags

}
///< end constructor

/// destructor
MultiReducedDiags::~MultiReducedDiags ()
{}
///< end destructor

/// call functions to compute diags
void MultiReducedDiags::ComputeDiags (int step)
{
    /// loop over all reduced diags
    for (int i_rd = 0; i_rd < m_rd_names.size(); ++i_rd)
    {
        m_multi_rd[i_rd] -> ComputeDiags(step);
    }
    ///< end loop over all reduced diags
}
///< end void MultiReducedDiags::ComputeDiags

/// funciton to write data
void MultiReducedDiags::WriteToFile (int step)
{

    /// Only the I/O rank does
    if ( !amrex::ParallelDescriptor::IOProcessor() ) { return; }

    /// loop over all reduced diags
    for (int i_rd = 0; i_rd < m_rd_names.size(); ++i_rd)
    {

        /// Judge if the diags should be done
        if ( (step+1) % m_multi_rd[i_rd]->m_freq != 0 ) { return; }

        /// call the write to file function
        m_multi_rd[i_rd]->WriteToFile(step);

    }
    ///< end loop over all reduced diags
}
///< end void MultiReducedDiags::WriteToFile
